from movielens_analysis import *

class TestLinks:
    # if the methods return the correct data types
    # if the lists elements have the correct data types
    # if the returned data sorted correctly

    MOVIE_LIST = list(range(10))

    @pytest.fixture(scope="class")
    def links_instance(self):
        links = Links("../datasets/links.csv", "../datasets/movies.csv")
        return links

    def test_init(self, links_instance):
        assert isinstance(links_instance.csv_links, dict)
        assert isinstance(links_instance.csv_movies, dict)

    def test__get_number(self, links_instance):
        unexpected_fields = links_instance.unexpected_fields

        assert links_instance._get_number("$30,000,000") == "30000000"
        assert links_instance._get_number("abc1.333.333bb") == "1333333"
        assert links_instance._get_number("") == unexpected_fields["Empty field"]
        assert links_instance._get_number("jjfjf") == unexpected_fields["Empty field"]

    def test__parse_valute(self, links_instance):
        unexpected_fields = links_instance.unexpected_fields

        assert links_instance._parse_valute("$30.300") == "30300"
        assert links_instance._parse_valute("abc") == unexpected_fields["Empty field"]
        assert (
            links_instance._parse_valute("13,233")
            == unexpected_fields["Unknown currency"]
        )

    def test__parse_time(self, links_instance):
        assert links_instance._parse_time("3 hour 5 minute") == 185
        assert links_instance._parse_time("0 hours 12 minutes") == 12
        assert links_instance._parse_time("1 hours") == 60
        assert links_instance._parse_time("55 minutes") == 55
        assert links_instance._parse_time("ff") == 0
        assert links_instance._parse_time("") == 0

    def test__get_soup_returns_soup(sefl, links_instance):
        """Проверяет, что _get_soup возвращает объект BeautifulSoup"""
        url = "https://example.com"
        soup = links_instance._get_soup(url, {})
        assert isinstance(
            soup, BeautifulSoup
        ), "Функция должна вернуть объект BeautifulSoup"

    def test__get_soup_raises_exception_on_bad_url(self, links_instance):
        """Проверяет, что _get_soup выбрасывает исключение, если URL недоступен"""
        bad_url = "https://thisurldofffffsdfesnotexist.com"

        with pytest.raises(Exception, match="An error occurred while"):
            links_instance._get_soup(bad_url, {})

    def test__csv_read(self, links_instance):
        key, val = next(iter(links_instance.csv_links.items()))
        assert isinstance(key, int)
        assert isinstance(val, str)

    def test_get_imdb(self, links_instance):
        imdb_info = links_instance.get_imdb(self.MOVIE_LIST)
        assert isinstance(imdb_info, list)
        assert isinstance(imdb_info[0], list)
        assert isinstance(imdb_info[0][0], int)
        for val in imdb_info[0]:
            assert isinstance(val, str) or isinstance(val, int)

        assert all(
            imdb_info[i][0] >= imdb_info[i + 1][0] for i in range(len(imdb_info) - 1)
        )

    def test_top_directors(self, links_instance):
        top_directors_info = links_instance.top_directors(3, self.MOVIE_LIST)
        top_directors_list = list(top_directors_info.items())

        assert isinstance(top_directors_info, dict)

        assert isinstance(top_directors_list[0][0], str)
        assert isinstance(top_directors_list[0][1], int)

        counts = list(top_directors_info.values())
        assert all(counts[i] >= counts[i + 1] for i in range(len(counts) - 1))

    def test_most_expensive(self, links_instance):
        most_expensive_info = links_instance.most_expensive(3, self.MOVIE_LIST)
        most_expensive_list = list(most_expensive_info.items())

        assert isinstance(most_expensive_info, dict)

        assert isinstance(most_expensive_list[0][0], str)
        assert isinstance(most_expensive_list[0][1], int)

        counts = list(most_expensive_info.values())
        assert all(counts[i] >= counts[i + 1] for i in range(len(counts) - 1))

    def test_most_profitable(self, links_instance):
        most_profitable_info = links_instance.most_profitable(3, self.MOVIE_LIST)
        most_profitable_list = list(most_profitable_info.items())

        assert isinstance(most_profitable_info, dict)

        assert isinstance(most_profitable_list[0][0], str)
        assert isinstance(most_profitable_list[0][1], int)

        counts = list(most_profitable_info.values())
        assert all(counts[i] >= counts[i + 1] for i in range(len(counts) - 1))

    def test_longest(self, links_instance):
        longest_info = links_instance.longest(3, self.MOVIE_LIST)
        longest_list = list(longest_info.items())

        assert isinstance(longest_info, dict)

        assert isinstance(longest_list[0][0], str)
        assert isinstance(longest_list[0][1], int)

        counts = list(longest_info.values())
        assert all(counts[i] >= counts[i + 1] for i in range(len(counts) - 1))

    def test_top_cost_per_minute(self, links_instance):
        top_cost_per_minute_info = links_instance.top_cost_per_minute(
            3, self.MOVIE_LIST
        )
        top_cost_per_minute_list = list(top_cost_per_minute_info.items())

        assert isinstance(top_cost_per_minute_info, dict)

        assert isinstance(top_cost_per_minute_list[0][0], str)
        assert isinstance(top_cost_per_minute_list[0][1], float)

        counts = list(top_cost_per_minute_info.values())
        assert all(counts[i] >= counts[i + 1] for i in range(len(counts) - 1))


class TestMovies:
    # if the methods return the correct data types
    # if the lists elements have the correct data types
    # if the returned data sorted correctly

    @pytest.fixture(scope="class")
    def links_instance(self):
        movies = Movies("../datasets/movies.csv")
        return movies

    def test_init(self, links_instance):
        assert isinstance(links_instance.csv_movies, dict)

    def test_dist_by_release(self, links_instance):
        info = links_instance.dist_by_release()

        assert isinstance(info, dict)

        info_items = list(info.items())

        assert isinstance(info_items[0][0], str)
        assert isinstance(info_items[0][1], int)
        assert all(
            info_items[i][1] >= info_items[i + 1][1] for i in range(len(info) - 1)
        )

    def test_dist_by_genres(self, links_instance):
        info = links_instance.dist_by_genres()

        assert isinstance(info, dict)

        info_items = list(info.items())

        assert isinstance(info_items[0][0], str)
        assert isinstance(info_items[0][1], int)
        assert all(
            info_items[i][1] >= info_items[i + 1][1] for i in range(len(info) - 1)
        )

    def test_most_genres(self, links_instance):
        info = links_instance.most_genres(5)

        assert isinstance(info, dict)

        info_items = list(info.items())

        assert isinstance(info_items[0][0], str)
        assert isinstance(info_items[0][1], int)
        assert all(
            info_items[i][1] >= info_items[i + 1][1] for i in range(len(info) - 1)
        )


class TestRatings:
    def test_average_type(self):
        assert isinstance(Ratings.average([1, 2, 3]), float)

    def test_average_elements_type(self):
        ratings = [1, 2, 3]
        result = Ratings.average(ratings)
        assert all(isinstance(i, (int, float)) for i in ratings)

    def test_average_correct_sort(self):
        ratings = [3, 1, 2]
        result = Ratings.average(ratings)
        assert result == 2

    def test_median_type(self):
        assert isinstance(Ratings.median([1, 2, 3, 4]), float)

    def test_median_elements_type(self):
        ratings = [1, 2, 3, 4]
        result = Ratings.median(ratings)
        assert all(isinstance(i, (int, float)) for i in ratings)

    def test_median_correct_sort(self):
        ratings = [3, 1, 2, 4]
        result = Ratings.median(ratings)
        assert result == 2.5

    def test_variance_type(self):
        assert isinstance(Ratings.variance([1, 2, 3]), float)

    def test_variance_elements_type(self):
        ratings = [1, 2, 3]
        result = Ratings.variance(ratings)
        assert all(isinstance(i, (int, float)) for i in ratings)

    def test_variance_correct_sort(self):
        ratings = [1, 2, 3]
        result = Ratings.variance(ratings)
        assert result == 0.67

    # Movies
    @pytest.fixture
    def ratings_instance(self):
        return Ratings()

    @pytest.fixture
    def movies_instance(self, ratings_instance):
        return Ratings.Movies(ratings_instance)

    # Test dist_by_year method
    def test_dist_by_year_type(self, movies_instance):
        result = movies_instance.dist_by_year()
        assert isinstance(result, dict)

    def test_dist_by_year_sorted(self, movies_instance):
        result = movies_instance.dist_by_year()
        assert list(result.keys()) == sorted(result.keys())

    def test_dist_by_year_elements_type(self, movies_instance):
        result = movies_instance.dist_by_year()
        assert all(isinstance(value, int) for value in result.values())

    # Test dist_by_rating method
    def test_dist_by_rating_type(self, movies_instance):
        result = movies_instance.dist_by_rating()
        assert isinstance(result, dict)

    def test_dist_by_rating_sorted(self, movies_instance):
        result = movies_instance.dist_by_rating()
        assert list(result.keys()) == sorted(result.keys())

    def test_dist_by_rating_elements_type(self, movies_instance):
        result = movies_instance.dist_by_rating()
        assert all(isinstance(value, int) for value in result.values())

    # Test top_by_num_of_ratings method
    def test_top_by_num_of_ratings_type(self, movies_instance):
        result = movies_instance.top_by_num_of_ratings(3)
        assert isinstance(result, dict)

    def test_top_by_num_of_ratings_sorted(self, movies_instance):
        result = movies_instance.top_by_num_of_ratings(3)
        assert list(result.values()) == sorted(result.values(), reverse=True)

    def test_top_by_num_of_ratings_elements_type(self, movies_instance):
        result = movies_instance.top_by_num_of_ratings(3)
        assert all(isinstance(value, int) for value in result.values())

    # Test top_by_ratings method
    def test_top_by_ratings_type(self, movies_instance):
        result = movies_instance.top_by_ratings(3, metric="average")
        assert isinstance(result, dict)

    def test_top_by_ratings_sorted(self, movies_instance):
        result = movies_instance.top_by_ratings(3, metric="average")
        assert list(result.values()) == sorted(result.values(), reverse=True)

    def test_top_by_ratings_elements_type(self, movies_instance):
        result = movies_instance.top_by_ratings(3, metric="average")
        assert all(isinstance(value, (float, int)) for value in result.values())

    def test_top_by_ratings_invalid_metric(self, movies_instance):
        with pytest.raises(ValueError):
            movies_instance.top_by_ratings(3, metric="invalid")

    # Test top_controversial method
    def test_top_controversial_type(self, movies_instance):
        result = movies_instance.top_controversial(3)
        assert isinstance(result, dict)

    def test_top_controversial_sorted(self, movies_instance):
        result = movies_instance.top_controversial(3)
        assert list(result.values()) == sorted(result.values(), reverse=True)

    def test_top_controversial_elements_type(self, movies_instance):
        result = movies_instance.top_controversial(3)
        assert all(isinstance(value, float) for value in result.values())

    # Users
    @pytest.fixture
    def users_instance(self, ratings_instance):
        return Ratings.Users(ratings_instance)

    # Test dist_by_num_of_ratings method
    def test_dist_by_num_of_ratings_type(self, users_instance):
        result = users_instance.dist_by_num_of_ratings()
        assert isinstance(result, dict)

    def test_dist_by_num_of_ratings_sorted(self, users_instance):
        result = users_instance.dist_by_num_of_ratings()
        assert list(result.keys()) == sorted(result.keys())

    def test_dist_by_num_of_ratings_elements_type(self, users_instance):
        result = users_instance.dist_by_num_of_ratings()
        assert all(isinstance(value, int) for value in result.values())

    # Test dist_by_avg_or_median_rating method
    def test_dist_by_avg_or_median_rating_type(self, users_instance):
        result = users_instance.dist_by_avg_or_median_rating()
        assert isinstance(result, dict)

    def test_dist_by_avg_or_median_rating_sorted(self, users_instance):
        result = users_instance.dist_by_avg_or_median_rating()
        assert list(result.keys()) == sorted(result.keys())

    def test_dist_by_avg_or_median_rating_elements_type(self, users_instance):
        result = users_instance.dist_by_avg_or_median_rating()
        assert all(isinstance(value, float) for value in result.values())

    # Test top_by_num_of_ratings method
    def test_top_by_num_of_ratings_type(self, users_instance):
        result = users_instance.top_by_num_of_ratings(3)
        assert isinstance(result, dict)

    def test_top_by_num_of_ratings_sorted(self, users_instance):
        result = users_instance.top_by_num_of_ratings(3)
        assert list(result.values()) == sorted(result.values(), reverse=True)

    def test_top_by_num_of_ratings_elements_type(self, users_instance):
        result = users_instance.top_by_num_of_ratings(3)
        assert all(isinstance(value, int) for value in result.values())

    # Test top_by_variance method
    def test_top_by_variance_type(self, users_instance):
        result = users_instance.top_by_variance(3)
        assert isinstance(result, dict)

    def test_top_by_variance_sorted(self, users_instance):
        result = users_instance.top_by_variance(3)
        assert list(result.values()) == sorted(result.values(), reverse=True)

    def test_top_by_variance_elements_type(self, users_instance):
        result = users_instance.top_by_variance(3)
        assert all(isinstance(value, float) for value in result.values())

    # Test top_controversial method
    def test_top_controversial_type(self, users_instance):
        result = users_instance.top_controversial(3)
        assert isinstance(result, dict)

    def test_top_controversial_sorted(self, users_instance):
        result = users_instance.top_controversial(3)
        assert list(result.values()) == sorted(result.values(), reverse=True)

    def test_top_controversial_elements_type(self, users_instance):
        result = users_instance.top_controversial(3)
        assert all(isinstance(value, float) for value in result.values())


class TestTags:
    @pytest.fixture
    def tags_instance(self):
        return Tags()

    # Test most_words method
    def test_most_words_type(self, tags_instance):
        result = tags_instance.most_words(5)
        assert isinstance(result, dict)

    def test_most_words_elements_type(self, tags_instance):
        result = tags_instance.most_words(5)
        assert all(isinstance(k, str) and isinstance(v, int) for k, v in result.items())

    def test_most_words_sorted(self, tags_instance):
        result = tags_instance.most_words(5)
        assert list(result.values()) == sorted(result.values(), reverse=True)

    # Test longest method
    def test_longest_type(self, tags_instance):
        result = tags_instance.longest(5)
        assert isinstance(result, list)

    def test_longest_elements_type(self, tags_instance):
        result = tags_instance.longest(5)
        assert all(isinstance(tag, str) for tag in result)

    def test_longest_sorted(self, tags_instance):
        result = tags_instance.longest(5)
        assert result == sorted(result, key=len, reverse=True)

    # Test most_words_and_longest method
    def test_most_words_and_longest_type(self, tags_instance):
        result = tags_instance.most_words_and_longest(5)
        assert isinstance(result, list)

    def test_most_words_and_longest_elements_type(self, tags_instance):
        result = tags_instance.most_words_and_longest(5)
        assert all(isinstance(tag, str) for tag in result)

    # Test most_popular method
    def test_most_popular_type(self, tags_instance):
        result = tags_instance.most_popular(5)
        assert isinstance(result, dict)

    def test_most_popular_elements_type(self, tags_instance):
        result = tags_instance.most_popular(5)
        assert all(isinstance(k, str) and isinstance(v, int) for k, v in result.items())

    def test_most_popular_sorted(self, tags_instance):
        result = tags_instance.most_popular(5)
        assert list(result.values()) == sorted(result.values(), reverse=True)

    # Test tags_with method
    def test_tags_with_type(self, tags_instance):
        result = tags_instance.tags_with("movie")
        assert isinstance(result, list)

    def test_tags_with_elements_type(self, tags_instance):
        result = tags_instance.tags_with("movie")
        assert all(isinstance(tag, str) for tag in result)

    def test_tags_with_sorted(self, tags_instance):
        result = tags_instance.tags_with("movie")
        assert result == sorted(result)
