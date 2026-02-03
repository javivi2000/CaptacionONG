import feedparser
import urllib.parse
from datetime import datetime, timedelta
import logging
from newspaper import Article
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("news_collector")

class NewsCollector:
    def __init__(self, country='ES', lang='es'):
        self.base_url = "https://news.google.com/rss/search?q={query}&hl={lang}&gl={country}&ceid={country}:{lang}"
        self.lang = lang
        self.country = country

    def search_company_news(self, company_name, municipality, period_days=7):
        """
        Busca noticias para una empresa obligatoriamente vinculadas a su municipio.
        """
        logger.info(f"Búsqueda estricta: '{company_name}' en '{municipality}'")
        results = self._perform_search(company_name, municipality, period_days)
        return results

    def _perform_search(self, company_name, municipality, period_days):
        # Limpiar nombre de empresa de caracteres raros
        clean_name = company_name.replace('"', '').strip()
        query = f'"{clean_name}"'
        if municipality:
            query += f' {municipality}'
            
        encoded_query = urllib.parse.quote(query)
        
        if period_days <= 7:
            when = "7d"
        elif period_days <= 30:
            when = "1m"
        else:
            when = "1y"
            
        full_query = f"{encoded_query}+when:{when}"
        url = self.base_url.format(query=full_query, lang=self.lang, country=self.country)
        
        logger.info(f"Consultando Google News: {query} (Periodo: {when})")
        
        feed = feedparser.parse(url)
        results = []
        now = datetime.now()
        limit_date = now - timedelta(days=period_days)

        if feed.entries:
            for entry in feed.entries:
                published_parsed = getattr(entry, 'published_parsed', None)
                pub_date = datetime(*published_parsed[:6]) if published_parsed else now
                if pub_date >= limit_date:
                    results.append({
                        "title": entry.title,
                        "link": entry.link,
                        "published": pub_date,
                        "source": entry.source.get('title', 'Google News') if hasattr(entry, 'source') else 'Google News'
                    })
        return results

    def extract_full_content(self, url):
        """Extrae el contenido completo de una noticia usando newspaper3k"""
        try:
            article = Article(url, language=self.lang)
            article.download()
            article.parse()
            return {
                "text": article.text,
                "summary": article.summary,
                "top_image": article.top_image,
                "authors": article.authors
            }
        except Exception as e:
            logger.warning(f"Error extrayendo contenido de {url}: {e}")
            return None
