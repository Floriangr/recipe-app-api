from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse("recipe:ingredient-list")


class PublicIngredientsApiTests(TestCase):
    """Test publicliy available ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test private ingredients API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user("test@london.com", "test1234")

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving ingredients for authenticated user"""
        Ingredient.objects.create(user=self.user, name="Milk")
        Ingredient.objects.create(user=self.user, name="Water")

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_authenticated_user(self):
        """Test that ingredients retrieved are limited to authenticated user"""
        user2 = get_user_model().objects.create_user("test2@london.com", "password")
        ingredient = Ingredient.objects.create(user=self.user, name="Egg")
        Ingredient.objects.create(user=user2, name="Potatoes")

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], ingredient.name)

    def test_create_ingredients_successful(self):
        """Test that ingredients can be created"""
        payload = {"name": "Asparagus"}
        self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user, name=payload["name"]
        ).exists()
        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """Test that creating invalid ingredient fails"""
        payload = {"name": ""}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assigned_to_recipes(self):
        """Test filtering ingredients that are assigned"""
        ingredient1 = Ingredient.objects.create(user=self.user, name="Apples")
        ingredient2 = Ingredient.objects.create(user=self.user, name="Flour")
        recipe = Recipe.objects.create(
            title="Apple Crumble",
            time_minutes=5,
            price=10,
            user=self.user,
        )
        recipe.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_ingredients_assigned_unique(self):
        """Test filtering ingredients by assigned returns unique items"""
        ingredient = Ingredient.objects.create(user=self.user, name="Eggs")
        Ingredient.objects.create(user=self.user, name="Cheese")
        recipe1 = Recipe.objects.create(
            title="Eggs Benedict",
            time_minutes=5,
            price=10,
            user=self.user,
        )
        recipe1.ingredients.add(ingredient)
        recipe2 = Recipe.objects.create(
            title="Bread",
            time_minutes=60,
            price=10,
            user=self.user,
        )
        recipe2.ingredients.add(ingredient)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
