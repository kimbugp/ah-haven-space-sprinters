import json

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from config.settings import default
from .models import Article
from .renderers import ArticleJSONRenderer
from .serializers import (
     ArticleSerializer
)

from authors.apps.profiles.models import Profile
from authors.apps.authentication.models import User


class ArticleView(ListCreateAPIView):
    """creating, viewing , deleting and updating articles"""

    permission_classes = (IsAuthenticatedOrReadOnly,)
    renderer_classes = (ArticleJSONRenderer, )

    def post(self, request):
        serializer_context = {'author': request.user.profile}
        article = request.data

        # Create an article from the above data
        serializer = ArticleSerializer(data=article, context=serializer_context)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        queryset = Article.objects.all()
        # the many param informs the serializer that it will be serializing more than a single article.
        serializer = ArticleSerializer(queryset, many=True)
        return Response({"articles": serializer.data})

class ArticleRetrieveUpdateDelete(RetrieveUpdateDestroyAPIView):

    permission_classes = (IsAuthenticatedOrReadOnly,)
    renderer_classes = (ArticleJSONRenderer, )
    serializer_class = ArticleSerializer
    queryset = Article.objects.all()
    lookup_field = 'slug'


    def get_object(self, *args, **kwargs):
        slug = self.kwargs.get("slug")
        return get_object_or_404(Article, slug=slug)


    def destroy(self, request, slug):

        article = self.get_object(slug)
        requester = Profile.objects.get(user=request.user)
        is_author = article.author == requester
        if not is_author:
            resp = {"message": "you can't delete this article"}
            return Response(resp,
                        status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(article)
        resp = {"message":"Article has been deleted"}
        return Response(resp)


    def update(self, request, slug):

        article = self.get_object(slug)
        requester = Profile.objects.get(user=request.user)
        is_author = article.author == requester
        if not is_author:
            resp = {"message": "you can't update this article"}
            return Response(resp,
                        status=status.HTTP_403_FORBIDDEN)

        serializer_data = request.data
        serializer = self.serializer_class(
            article, data=serializer_data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
