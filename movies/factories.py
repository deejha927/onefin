from django.contrib.auth.models import User
from .models import *
import factory
import uuid


class UserFactory(factory.django.DjangoModelFactory):
    """
    Factory class for creating User instances.
    """
    class Meta:
        model = User

    username = factory.Faker('user_name')
    password = factory.Faker('password')


class MovieFactory(factory.django.DjangoModelFactory):
    """
    Factory class for creating Movie instances.
    """
    class Meta:
        model = Movie

    title = factory.Faker('sentence')
    description = factory.Faker('text')
    genres = factory.Faker('word')
    uuid = factory.LazyFunction(uuid.uuid4)


class CollectionFactory(factory.django.DjangoModelFactory):
    """
    Factory class for creating Collection instances.
    """
    class Meta:
        model = Collection

    title = factory.Faker('sentence')
    description = factory.Faker('text')
    uuid = factory.LazyFunction(uuid.uuid4)
    user = factory.SubFactory(UserFactory)

    @factory.post_generation
    def movies(self, create, extracted, **kwargs):
        """
        Post-generation hook to add movies to the collection.
        If `extracted` is provided, it adds the extracted movies to the collection.
        Otherwise, it creates default movies using the MovieFactory.
        """
        if not create:
            return
        if extracted:
            for movie in extracted:
                self.movies.add(movie)
        else:
            # Create some default movies for the collection
            movie1 = MovieFactory()
            movie2 = MovieFactory()
            self.movies.add(movie1, movie2)
