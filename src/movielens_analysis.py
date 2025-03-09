import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytest
import json


class Constans:
    UNEXPECTED_FIELDS = {
        "Empty field": "-",
        "Unknown currency": "Unknown currency",
        "Invalid year": "0000",
    }


class Tools:
    def printd(self, dict, title="", title0="", n=5):
        for k, v in list(dict.items())[:n]:
            print(f"{title0}{k}: {v}{title}")
    
    def printl(self, list, n=5):
        for i in list[:n]:
            print(i)


class CSVTools:
    def parse_csv_line(self, line: str) -> list[str]:
        """
        1,"hello, world",44,g

        ->

        ["1", "hello, world", "44", "g"]
        """

        i = 0
        fields = []
        field = []
        inside_quotes = False
        len_line = len(line)
        while i < len(line):
            char = line[i]
            if char == '"':
                if i + 2 < len_line and line[i + 1] == '"' and line[i + 2] != ",":
                    field.append('"')
                    i += 1
                else:
                    inside_quotes = not inside_quotes
            elif char == "," and not inside_quotes:
                fields.append("".join(field))
                field = []
            elif char != "\n":
                field.append(char)

            i += 1

        if inside_quotes:
            raise ValueError(f"Непарные кавычки в строке: {line}")

        fields.append("".join(field))
        return fields

    def read_csv(
        self, path, header=True, start_col=1, end_col=None
    ) -> dict[int, list[str]]:
        """ "
        Read specific csv file and return dict.
        The first element must be an immutable data structure.

        Id, field1, field2, field3
        1,"hello, world",44,g
        69,"uwu,333,papa

        ->

        {
        1: ["hello", "44", "g"]
        69: ["uwu", "333", "papa"]
        }
        """

        try:
            data = []
            with open(path, "r") as file:
                if header:
                    next(file)
                data = [
                    self.parse_csv_line(line.strip()) for line in file if line.strip()
                ]

            result = {
                int(row[0]): row[start_col:end_col]
                for row in data
                if row and row[0].isdigit()
            }
        except Exception as e:
            print(f"{e}")
            return {}
        return result

    def read_csv_col(self, path, headers=True, col=1):
        csv_info = self.read_csv(path, headers, col, col + 1)
        return {k: (v[0] if v else None) for k, v in csv_info.items()}


class Links:
    """
    Analyzing data from links.csv
    """

    def __init__(
        self,
        path_to_the_file_links="../datasets/links.csv",
        path_to_the_file_movies="../datasets/movies.csv",
    ):
        self.csv_links = self._csv_read(path_to_the_file_links)
        self.csv_movies = self._csv_read(path_to_the_file_movies)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://finance.yahoo.com",
        }
        self.indices_fields = {
            "Director": 1,
            "Budget": 2,
            "Cumulative Worldwide Gross": 3,
            "Runtime": 4,
        }

        self.correct_fields = list(self.indices_fields.keys())
        self.unexpected_fields = Constans.UNEXPECTED_FIELDS
        self.unexpected_fields_set = set(self.unexpected_fields.values())
        self.cache_dir = "cache"

    def _get_number(self, str_number) -> str:
        match = re.search(r"[\d,.]+", str_number)
        return (
            match.group().replace(",", "").replace(".", "")
            if match
            else self.unexpected_fields["Empty field"]
        )

    def _parse_valute(self, str_number) -> int:
        exchange_rate_to_dollar = {
            "£": 1.24,  # Британский фунт
            "€": 1.04,  # Евро
            "CA$": 1.449,  # Канадский доллар
            "AU$": 1.50,  # Австралийский доллар
            "¥": 0.0068,  # Японская иена
            "₩": 0.00075,  # Южнокорейская вона
            "₹": 0.012,  # Индийская рупия
            "₽": 0.011,  # Российский рубль (курс примерный)
            "CHF": 1.13,  # Швейцарский франк
            "HK$": 0.13,  # Гонконгский доллар
            "SG$": 0.74,  # Сингапурский доллар
            "NZ$": 0.62,  # Новозеландский доллар
            "$": 1.0,  # Доллар США
        }

        number = self._get_number(str_number)
        if number == self.unexpected_fields["Empty field"]:
            return self.unexpected_fields["Empty field"]

        for symbol, rate in exchange_rate_to_dollar.items():
            if symbol in str_number:
                return str(int(int(number) * rate))

        return self.unexpected_fields["Unknown currency"]

    def _parse_time(self, str_time: str) -> int:
        """
        - "2 hours 4 minutes" -> 124
        - "1 hour 4 minutes" -> 64
        - "2 hours" -> 120
        - "1 hour" -> 60
        - "4 minutes" -> 4
        - "" -> 0
        - "fjlfjk" -> 0
        """

        hours, minutes = 0, 0

        match_hours = re.search(r"(\d+)\s*hour[s]?", str_time)
        match_minutes = re.search(r"(\d+)\s*minute[s]?", str_time)

        if match_hours:
            hours = int(match_hours.group(1))
        if match_minutes:
            minutes = int(match_minutes.group(1))

        return hours * 60 + minutes

    def _get_soup(self, url, headers):
        def _cache_file_path(url):
            safe_name = url.replace("https://", "").replace("http://", "")
            for ch in ["/", "?", "=", "&", ":", "."]:
                safe_name = safe_name.replace(ch, "_")
            safe_name = safe_name[:120]
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir)
            return os.path.join(self.cache_dir, safe_name + ".html")

        cache_path = _cache_file_path(url)

        try:
            # Пытаемся сначала прочитать из кэша, если файл существует
            if os.path.exists(cache_path):
                with open(cache_path, "r", encoding="utf-8") as f:
                    html = f.read()
                # print(f"Using cached HTML for: {url}")
                return BeautifulSoup(html, "html.parser")

            # print(f"Fetching: {url}")
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()

            html = resp.text
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(html)

            return BeautifulSoup(html, "html.parser")
        except Exception as e:
            print(f"Error: {str(e)}")
            print(f"url: {url}, cache_path: {cache_path}")
            raise Exception(
                f"An error occurred while processing the URL: {url} and cache path: {cache_path}. Error: {e}"
            )

    def _csv_read(self, path_to_the_file) -> dict[int, str]:
        csv_data = {}
        try:
            with open(path_to_the_file, "r") as file:
                next(file)
                for line in file:
                    if ',"' in line and '",' in line:
                        parts = line.split(',"', 1)
                        movieId = int(parts[0])
                        field = parts[1].rsplit('",', 1)[0]
                    else:
                        parts = line.split(",")
                        movieId = int(parts[0])
                        field = parts[1]
                    csv_data[movieId] = field
        except Exception as e:
            print(f"{e}")
        return csv_data

    def save_to_json(self, data, filename):
        """
        Сохраняет данные в JSON-файл.
        """

        with open(filename, "w") as f:
            json.dump(data, f)
        print(f"Данные сохранены в файл {filename}")

    def load_from_json(self, filename):
        """
        Загружает данные из JSON-файла.
        """

        with open(filename, "r") as f:
            data = json.load(f)
        print(f"Данные загружены из файла {filename}")
        return data

    def parse_all_data_to_csv(self, output_file_name):
        def escape_csv_field(field):
            field = str(field)
            if "," in field or '"' in field:
                field = field.replace('"', '""')
                return f'"{field}"'
            return field

        data = self.get_imdb()
        try:
            with open(output_file_name, "w") as file:
                line = "movieId," + ",".join(self.correct_fields) + "\n"
                file.write(line)
                for row in data:
                    line = ",".join(escape_csv_field(elem) for elem in row) + "\n"
                    file.write(line)
        except Exception as e:
            print(f"{e}")

    def get_imdb_movie(self, movie: int, list_of_fields: list[str]):
        imdb_movie_info = [movie]

        if movie not in self.csv_links:
            print(f"Error movie {movie} missing from csv_links")
            return [movie] + [self.unexpected_fields["Empty field"]] * 4

        soup = None
        if any(field in list_of_fields for field in self.correct_fields):
            url = f"https://www.imdb.com/title/tt{self.csv_links[movie]}/"
            try:
                soup = self._get_soup(url, headers=self.headers)
            except Exception as e:
                print(f"Error fetching data for movie {movie}: {e}")
                return [movie] + [self.unexpected_fields["Empty field"]] * 4

        def extract_data(block_selector: str, use_div=False):
            if soup is None:
                return self.unexpected_fields["Empty field"]
            block = soup.find("li", {"data-testid": block_selector})
            if block:
                if use_div:
                    text = block.find("div")
                else:
                    text = block.find(
                        "span", class_="ipc-metadata-list-item__list-content-item"
                    )
                if text and text.text:
                    return text.text.strip()
            return self.unexpected_fields["Empty field"]

        if "Director" in list_of_fields:
            if soup is None:  # Проверка, что soup определен
                imdb_movie_info.append(self.unexpected_fields["Empty field"])
            director_block = soup.find(
                "li", {"data-testid": "title-pc-principal-credit"}
            )
            if director_block:
                director_names = [
                    a.text.strip()
                    for a in director_block.find_all(
                        "a", class_="ipc-metadata-list-item__list-content-item"
                    )
                ]
                imdb_movie_info.append(
                    ", ".join(director_names)
                    if director_names
                    else self.unexpected_fields["Empty field"]
                )
            else:
                imdb_movie_info.append(self.unexpected_fields["Empty field"])
        if "Budget" in list_of_fields:
            text = extract_data("title-boxoffice-budget")
            imdb_movie_info.append(self._parse_valute(text))
        if "Cumulative Worldwide Gross" in list_of_fields:
            text = extract_data("title-boxoffice-cumulativeworldwidegross")
            imdb_movie_info.append(self._parse_valute(text))
        if "Runtime" in list_of_fields:
            imdb_movie_info.append(
                self._parse_time(extract_data("title-techspec_runtime", use_div=True))
            )
        return imdb_movie_info

    def get_imdb(
        self,
        list_of_movies: list[int] = None,
        list_of_fields: list[str] = None,
        default_movie_limit=500,
    ):
        """
        The method returns a list of lists [movieId, field1, field2, field3, ...] for the list of movies given as the argument (movieId).
        For example, [movieId, Director, Budget, Cumulative Worldwide Gross, Runtime].
        The values should be parsed from the IMDB webpages of the movies.
        Sort it by movieId descendingly.

        Example:
        get_imdb(["1", "2"], ["Director", "Budget"]) ->
        [
            ["2", "Tim Burton", "$50 млн"],
            ["1", "John Lasseter", "$30 млн"]
        ]
        """

        if list_of_movies is None:
            list_of_movies = list(self.csv_links.keys())[:default_movie_limit]
        if list_of_fields is None:
            list_of_fields = self.correct_fields

        imdb_info = [
            self.get_imdb_movie(int(movieId), list_of_fields)
            for movieId in list_of_movies
        ]
        return sorted(imdb_info, key=lambda x: -x[0])

    def print_imdb_info(self, imdb_info):
        l = len(imdb_info)
        print("movieId," + ",".join(self.correct_fields))
        limit = 10
        if l < limit:
            for i in range(l):
                print(imdb_info[i])
        else:
            for i in range(0, limit // 2):
                print(imdb_info[i])
            for i in range(l - limit // 2, l):
                print(imdb_info[i])

    def top_directors(
        self,
        n,
        list_of_movies: list[int] = None,
        imdb_info=None,
        default_movie_limit=500,
    ):
        """
        The method returns a dict with top-n directors where the keys are directors and
        the values are numbers of movies created by them. Sort it by numbers descendingly.
        """

        if imdb_info == None:
            info = self.get_imdb(list_of_movies, ["Director"], default_movie_limit)
        else:
            index_director = self.indices_fields["Director"]
            info = [[part[0], part[index_director]] for part in imdb_info]

        directors = {}

        for part in info:
            if part[1] != self.unexpected_fields["Empty field"]:
                director_names = [name.strip() for name in part[1].split(",")]
                for director in director_names:
                    directors[director] = directors.get(director, 0) + 1

        return dict(sorted(directors.items(), key=lambda x: -x[1])[:n])

    def most_expensive(
        self,
        n,
        list_of_movies: list[int] = None,
        imdb_info=None,
        default_movie_limit=500,
    ):
        """
        The method returns a dict with top-n movies where the keys are movie titles and
        the values are their budgets. Sort it by budgets descendingly.
        """

        if imdb_info == None:
            info = self.get_imdb(list_of_movies, ["Budget"], default_movie_limit)
        else:
            index_budget = self.indices_fields["Budget"]
            info = [[part[0], part[index_budget]] for part in imdb_info]

        budgets = {
            self.csv_movies.get(part[0], "Unknown Title"): int(part[1])
            for part in info
            if part[1] not in self.unexpected_fields_set
        }

        return dict(sorted(budgets.items(), key=lambda x: -int(x[1]))[:n])

    def most_profitable(
        self,
        n,
        list_of_movies: list[int] = None,
        imdb_info=None,
        default_movie_limit=500,
    ):
        """
        The method returns a dict with top-n movies where the keys are movie titles and
        the values are the difference between cumulative worldwide gross and budget.
        Sort it by the difference descendingly.
        """

        if imdb_info == None:
            info = self.get_imdb(
                list_of_movies,
                ["Budget", "Cumulative Worldwide Gross"],
                default_movie_limit,
            )
        else:
            index_1 = self.indices_fields["Budget"]
            index_2 = self.indices_fields["Cumulative Worldwide Gross"]
            info = [[part[0], part[index_1], part[index_2]] for part in imdb_info]

        profits = {
            self.csv_movies[part[0]]: int(part[2]) - int(part[1])
            for part in info
            if (
                part[1] not in self.unexpected_fields_set
                and part[2] not in self.unexpected_fields_set
            )
        }

        return dict(sorted(profits.items(), key=lambda x: -int(x[1]))[:n])

    def longest(
        self,
        n,
        list_of_movies: list[int] = None,
        imdb_info=None,
        default_movie_limit=500,
    ):
        """
        The method returns a dict with top-n movies where the keys are movie titles and
        the values are their runtime. If there are more than one version – choose any.
        Sort it by runtime descendingly.
        """

        if imdb_info == None:
            info = self.get_imdb(list_of_movies, ["Runtime"], default_movie_limit)
        else:
            index_runtime = self.indices_fields["Runtime"]
            info = [[part[0], part[index_runtime]] for part in imdb_info]

        runtimes = {
            self.csv_movies[part[0]]: int(part[1])
            for part in info
            if part[1] not in self.unexpected_fields_set
        }

        return dict(sorted(runtimes.items(), key=lambda x: -x[1])[:n])

    def top_cost_per_minute(
        self,
        n,
        list_of_movies: list[int] = None,
        imdb_info=None,
        default_movie_limit=500,
    ):
        """
        The method returns a dict with top-n movies where the keys are movie titles and
        the values are the budgets divided by their runtime. The budgets can be in different currencies – do not pay attention to it.
        The values should be rounded to 2 decimals. Sort it by the division descendingly.
        """

        if imdb_info == None:
            info = self.get_imdb(
                list_of_movies, ["Budget", "Runtime"], default_movie_limit
            )
        else:
            index_1 = self.indices_fields["Budget"]
            index_2 = self.indices_fields["Runtime"]
            info = [[part[0], part[index_1], part[index_2]] for part in imdb_info]

        costs = {
            self.csv_movies[part[0]]: round(int(part[1]) / int(part[2]), 2)
            for part in info
            if (
                part[1] not in self.unexpected_fields_set
                and part[2] not in self.unexpected_fields_set
            )
        }

        return dict(sorted(costs.items(), key=lambda x: -x[1])[:n])


class Movies:
    """
    Analyzing data from movies.csv
    """

    def __init__(self, path_to_the_file_movies):
        self.csv = CSVTools()
        self.csv_movies = self.csv.read_csv(path_to_the_file_movies)
        self.unexpected_fields = Constans.UNEXPECTED_FIELDS
        self.unexpected_fields_set = set(self.unexpected_fields.values())

    def _extract_year(self, line: str) -> str:
        match = re.search(r"\((\d{4})\)", line)
        return match.group(1) if match else self.unexpected_fields["Empty field"]

    def _extract_genres(self, line: str) -> list[str]:
        return line.split("|")

    def dist_by_release(self) -> dict[str, int]:
        """
        The method returns a dict or an OrderedDict where the keys are years and the values are counts.
        You need to extract years from the titles. Sort it by counts descendingly.
        """

        release_years = {}

        for value in self.csv_movies.values():
            year = self._extract_year(value[0])
            release_years[year] = release_years.get(year, 0) + 1

        return dict(sorted(release_years.items(), key=lambda x: -x[1]))

    def dist_by_genres(self) -> dict[str, int]:
        """
        The method returns a dict where the keys are genres and the values are counts.
        Sort it by counts descendingly.
        """

        genres = {}

        for value in self.csv_movies.values():
            for genre in self._extract_genres(value[1]):
                genres[genre] = genres.get(genre, 0) + 1

        return dict(sorted(genres.items(), key=lambda x: -x[1]))

    def most_genres(self, n) -> dict[str, int]:
        """
        The method returns a dict with top-n movies where the keys are movie titles and
        the values are the number of genres of the movie. Sort it by numbers descendingly.
        """

        movies = {}

        for value in self.csv_movies.values():
            title = value[0]
            count_genres = len(set(self._extract_genres(value[1])))
            movies[title] = count_genres

        return dict(sorted(movies.items(), key=lambda x: -x[1])[:n])


class Ratings:
    """
    Analyzing data from ratings.csv
    """

    def __init__(self, path="../datasets/ratings.csv"):
        """
        Put here any fields that you think you will need.
        """
        self.path = path

    @staticmethod
    def average(ratings):
        """
        Calculate the average of a list of ratings.
        """
        return round(sum(ratings) / len(ratings), 2)

    @staticmethod
    def median(ratings):
        """
        Calculate the median of a list of ratings.
        """
        ratings_sorted = sorted(ratings)
        n = len(ratings_sorted)
        mid = n // 2
        if n % 2 == 1:
            return round(ratings_sorted[mid], 2)
        else:
            return round((ratings_sorted[mid - 1] + ratings_sorted[mid]) / 2, 2)

    @staticmethod
    def variance(ratings):
        """
        Calculate the variance of a list of ratings.
        """
        mean = sum(ratings) / len(ratings)
        return round(sum((x - mean) ** 2 for x in ratings) / len(ratings), 2)

    class Movies:
        def __init__(self, parent):
            self.parent = parent
            self.path = parent.path

        def _read_movie_titles(self):
            movie_titles = {}
            try:
                with open("../datasets/movies.csv", "r") as f:
                    next(f)
                    for line in f:
                        movieId, title, _ = line.strip().split(",", 2)
                        movie_titles[int(movieId)] = title
            except ValueError:
                raise Exception("error")
            return movie_titles

        def _read_ratings(self):
            ratings = []
            try:
                with open(self.path, "r") as f:
                    next(f)
                    for line in f:
                        userId, movieId, rating, timestamp = line.strip().split(",")
                        ratings.append(
                            (int(userId), int(movieId), float(rating), int(timestamp))
                        )
            except ValueError:
                print(f"Skipping invalid line: {line.strip()}")
            return ratings

        def dist_by_year(self):
            """
            The method returns a dict where the keys are years and the values are counts.
            Sort it by years ascendingly. You need to extract years from timestamps.
            """
            try:
                ratings_by_year = {}
                for _, _, _, timestamp in self._read_ratings():
                    year = datetime.fromtimestamp(timestamp).year
                    if year in ratings_by_year:
                        ratings_by_year[year] += 1
                    else:
                        ratings_by_year[year] = 1
                return dict(sorted(ratings_by_year.items()))
            except ValueError:
                raise Exception("error")

        def dist_by_rating(self):
            """
            The method returns a dict where the keys are ratings and the values are counts.
            Sort it by ratings ascendingly.
            """
            try:
                ratings_distribution = {}
                for _, _, rating, _ in self._read_ratings():
                    if rating in ratings_distribution:
                        ratings_distribution[rating] += 1
                    else:
                        ratings_distribution[rating] = 1
            except ValueError:
                raise Exception("error")
            return dict(sorted(ratings_distribution.items()))

        def top_by_num_of_ratings(self, n):
            """
            The method returns top-n movies by the number of ratings.
            It is a dict where the keys are movie titles and the values are numbers.
            Sort it by numbers descendingly.
            """
            try:
                movie_ratings_counts = {}
                for _, movieId, _, _ in self._read_ratings():
                    if movieId in movie_ratings_counts:
                        movie_ratings_counts[movieId] += 1
                    else:
                        movie_ratings_counts[movieId] = 1

                movie_titles = self._read_movie_titles()
                sorted_movies = sorted(
                    movie_ratings_counts.items(), key=lambda x: x[1], reverse=True
                )

                top_movies = {}
                for i in range(min(n, len(sorted_movies))):
                    movieId = sorted_movies[i][0]
                    top_movies[movie_titles.get(movieId)] = sorted_movies[i][1]
            except ValueError:
                raise Exception("error")
            return top_movies

        def top_by_ratings(self, n, metric="average"):
            """
            The method returns top-n movies by the average or median of the ratings.
            It is a dict where the keys are movie titles and the values are metric values.
            Sort it by metric descendingly.
            The values should be rounded to 2 decimals.
            """
            if metric not in ["average", "median"]:
                raise ValueError("Metric must be 'average' or 'median'")

            movie_ratings = {}
            for _, movieId, rating, _ in self._read_ratings():
                if movieId in movie_ratings:
                    movie_ratings[movieId].append(rating)
                else:
                    movie_ratings[movieId] = [rating]

            if metric == "average":
                movie_scores = {
                    movieId: Ratings.average(ratings)
                    for movieId, ratings in movie_ratings.items()
                }
            else:
                movie_scores = {
                    movieId: Ratings.median(ratings)
                    for movieId, ratings in movie_ratings.items()
                }

            movie_titles = self._read_movie_titles()
            sorted_movies = sorted(
                movie_scores.items(), key=lambda x: x[1], reverse=True
            )

            top_movies = {}
            for i in range(min(n, len(sorted_movies))):
                movieId = sorted_movies[i][0]
                top_movies[movie_titles.get(movieId)] = sorted_movies[i][1]
            return top_movies

        def top_controversial(self, n):
            """
            The method returns top-n movies by the variance of the ratings.
            It is a dict where the keys are movie titles and the values are the variances.
            Sort it by variance descendingly.
            The values should be rounded to 2 decimals.
            """
            try:
                movie_ratings = {}
                for _, movieId, rating, _ in self._read_ratings():
                    if movieId in movie_ratings:
                        movie_ratings[movieId].append(rating)
                    else:
                        movie_ratings[movieId] = [rating]

                movie_variances = {
                    movieId: Ratings.variance(ratings)
                    for movieId, ratings in movie_ratings.items()
                }

                movie_titles = self._read_movie_titles()
                sorted_movies = sorted(
                    movie_variances.items(), key=lambda x: x[1], reverse=True
                )

                top_movies = {
                    movie_titles[movieId]: var
                    for movieId, var in sorted_movies[:n]
                    if movieId in movie_titles
                }
            except ValueError:
                raise Exception("error")
            return top_movies

    class Users(Movies):
        """
        In this class, three methods should work.
        The 1st returns the distribution of users by the number of ratings made by them.
        The 2nd returns the distribution of users by average or median ratings made by them.
        The 3rd returns top-n users with the biggest variance of their ratings.
        Inherit from the class Movies. Several methods are similar to the methods from it.
        """

        def dist_by_num_of_ratings(self):
            """
            The method returns a dict where the keys are users and the values are the number of ratings they made.
            Sort it by users ascendingly.
            """
            try:
                user_ratings_counts = {}
                for userId, _, _, _ in self._read_ratings():
                    if userId in user_ratings_counts:
                        user_ratings_counts[userId] += 1
                    else:
                        user_ratings_counts[userId] = 1
            except ValueError:
                raise Exception("error")
            return dict(sorted(user_ratings_counts.items()))

        def dist_by_avg_or_median_rating(self, metric="average"):
            """
            The method returns a dict where the keys are users and the values are the average or median ratings they made.
            Sort it by users ascendingly.
            The values should be rounded to 2 decimals.
            """
            try:
                if metric not in ["average", "median"]:
                    raise ValueError("Metric must be 'average' or 'median'")

                user_ratings = {}
                for userId, _, rating, _ in self._read_ratings():
                    if userId in user_ratings:
                        user_ratings[userId].append(rating)
                    else:
                        user_ratings[userId] = [rating]

                if metric == "average":
                    user_scores = {
                        userId: Ratings.average(ratings)
                        for userId, ratings in user_ratings.items()
                    }
                else:
                    user_scores = {
                        userId: Ratings.median(ratings)
                        for userId, ratings in user_ratings.items()
                    }
            except ValueError:
                raise Exception("error")
            return dict(sorted(user_scores.items()))

        def top_by_variance(self, n):
            """
            The method returns top-n users with the biggest variance of their ratings.
            It is a dict where the keys are users and the values are the variances.
            Sort it by variance descendingly.
            The values should be rounded to 2 decimals.
            """
            try:
                user_ratings = {}
                for userId, _, rating, _ in self._read_ratings():
                    if userId in user_ratings:
                        user_ratings[userId].append(rating)
                    else:
                        user_ratings[userId] = [rating]

                user_variances = {
                    userId: Ratings.variance(ratings)
                    for userId, ratings in user_ratings.items()
                }

                sorted_users = sorted(
                    user_variances.items(), key=lambda x: x[1], reverse=True
                )

                top_users = {userId: var for userId, var in sorted_users[:n]}
            except ValueError:
                raise Exception("error")
            return top_users


class Tags:
    """
    Analyzing data from tags.csv
    """

    def __init__(self, path="../datasets/tags.csv"):
        """
        Put here any fields that you think you will need.
        """
        self.path = path

    def most_words(self, n):
        """
               The method returns top-n tags with most words inside. It is a dict
        where the keys are tags and the values are the number of words inside the tag.
        Drop the duplicates. Sort it by numbers descendingly.
        """
        try:
            all_tags_counts_word = {}  # словарь со всеми тэгами и количеством слов
            with open(self.path, "r") as f:
                next(f)
                for line in f:
                    try:
                        _, _, tag, _ = line.strip().split(",")
                        all_tags_counts_word[tag] = len(tag.split())
                    except ValueError:
                        print(f"Skipping invalid line: {line.strip()}")

            big_tags = dict(
                sorted(all_tags_counts_word.items(), key=lambda x: x[1], reverse=True)
            )
        except ValueError:
            raise Exception("error")
        return dict(list(big_tags.items())[:n])

    def longest(self, n):
        """
        The method returns top-n longest tags in terms of the number of characters.
        It is a list of the tags. Drop the duplicates. Sort it by numbers descendingly.
        """
        try:
            all_tags_counts_word = {}  # словарь со всеми тэгами и количеством слов
            with open(self.path, "r") as f:
                next(f)
                for line in f:
                    try:
                        _, _, tag, _ = line.strip().split(",")
                        all_tags_counts_word[tag] = len(tag)
                    except ValueError:
                        print(f"Skipping invalid line: {line.strip()}")

            big_tags = list(
                sorted(all_tags_counts_word.keys(), key=lambda x: len(x), reverse=True)
            )
        except ValueError:
            raise Exception("error")
        return big_tags[:n]

    def most_words_and_longest(self, n):
        """
        The method returns the intersection between top-n tags with most words inside and
        top-n longest tags in terms of the number of characters.
        Drop the duplicates. It is a list of the tags.
        """
        try:
            most_words_tags = set(self.most_words(n).keys())
            longest_tags = set(self.longest(n))
        except ValueError:
            raise Exception("error")
        return list(most_words_tags & longest_tags)

    def most_popular(self, n):
        """
        The method returns the most popular tags.
        It is a dict where the keys are tags and the values are the counts.
        Drop the duplicates. Sort it by counts descendingly.
        """
        try:
            popular_tags = {}
            with open(self.path, "r") as f:
                next(f)
                for line in f:
                    try:
                        _, _, tag, _ = line.strip().split(",")
                        if tag in popular_tags:
                            popular_tags[tag] += 1
                        else:
                            popular_tags[tag] = 1
                    except ValueError:
                        print(f"Skipping invalid line: {line.strip()}")
            popular_tags = dict(
                sorted(popular_tags.items(), key=lambda x: x[1], reverse=True)
            )
        except ValueError:
            raise Exception("error")
        return dict(list(popular_tags.items())[:n])

    def tags_with(self, word):
        """
        The method returns all unique tags that include the word given as the argument.
        Drop the duplicates. It is a list of the tags. Sort it by tag names alphabetically.
        """
        try:
            tags_with_word = []
            with open(self.path, "r") as f:
                next(f)
                for line in f:
                    try:
                        _, _, tag, _ = line.strip().split(",")
                        if word in tag and tag not in tags_with_word:
                            tags_with_word.append(tag)
                    except ValueError:
                        print(f"Skipping invalid line: {line.strip()}")
            if len(tags_with_word) != 0:
                tags_with_word.sort()
            else:
                raise Exception("No tags with this word")
        except ValueError:
            raise Exception("error")
        return tags_with_word
