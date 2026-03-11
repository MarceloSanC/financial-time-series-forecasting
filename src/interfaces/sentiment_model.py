# src/interfaces/sentiment_model.py

from abc import ABC, abstractmethod

from src.entities.news_article import NewsArticle
from src.entities.scored_news_article import ScoredNewsArticle


class SentimentModel(ABC):
    @abstractmethod
    def infer(
        self,
        articles: list[NewsArticle],
    ) -> list[ScoredNewsArticle]:
        """
        Infere sentimento quantitativo para cada notícia.
        """
        ...
