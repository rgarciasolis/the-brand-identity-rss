#!/usr/bin/env python3
"""
RSS Generator para The Brand Identity
Scrapea the-brandidentity.com/features y genera RSS feed
"""

import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import re
import json
import os
from urllib.parse import urljoin, urlparse

class TheBrandIdentityRSS:
    def __init__(self):
        self.base_url = "https://the-brandidentity.com"
        self.features_url = "https://the-brandidentity.com/features"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def fetch_articles(self):
        """Obtiene los artículos de la página de features"""
        try:
            print(f"Fetching: {self.features_url}")
            response = self.session.get(self.features_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Buscar artículos - ajustar selectores según la estructura real
            article_elements = soup.find_all(['article', 'div'], class_=re.compile(r'(post|article|item|card|entry)'))
            
            if not article_elements:
                # Fallback: buscar por enlaces que parecen artículos
                article_elements = soup.find_all('a', href=re.compile(r'/[^/]+/?$'))
                
            print(f"Found {len(article_elements)} potential articles")
            
            for element in article_elements[:20]:  # Limitamos a 20 artículos
                article = self.extract_article_data(element)
                if article:
                    articles.append(article)
                    
            return articles
            
        except Exception as e:
            print(f"Error fetching articles: {e}")
            return []
    
    def extract_article_data(self, element):
        """Extrae datos de un elemento artículo"""
        try:
            # Buscar título
            title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'a'])
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            if not title or len(title) < 10:
                return None
            
            # Buscar URL
            link_elem = element.find('a') or element
            if link_elem.name == 'a':
                url = link_elem.get('href')
            else:
                url = element.find('a', href=True)
                url = url['href'] if url else None
                
            if not url:
                return None
                
            url = urljoin(self.base_url, url)
            
            # Buscar descripción
            desc_elem = element.find(['p', 'div'], class_=re.compile(r'(excerpt|description|summary)'))
            if not desc_elem:
                desc_elem = element.find('p')
                
            description = desc_elem.get_text(strip=True) if desc_elem else title
            
            # Buscar imagen
            img_elem = element.find('img')
            image_url = None
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src')
                if image_url:
                    image_url = urljoin(self.base_url, image_url)
            
            # Fecha (usar fecha actual si no se encuentra)
            pub_date = datetime.now(timezone.utc)
            
            return {
                'title': title,
                'url': url,
                'description': description,
                'image_url': image_url,
                'pub_date': pub_date,
                'guid': url
            }
            
        except Exception as e:
            print(f"Error extracting article data: {e}")
            return None
    
    def generate_rss(self, articles):
        """Genera el XML RSS"""
        # Crear elemento raíz RSS
        rss = ET.Element('rss', version='2.0')
        rss.set('xmlns:content', 'http://purl.org/rss/1.0/modules/content/')
        rss.set('xmlns:dc', 'http://purl.org/dc/elements/1.1/')
        rss.set('xmlns:media', 'http://search.yahoo.com/mrss/')
        
        channel = ET.SubElement(rss, 'channel')
        
        # Metadatos del canal
        ET.SubElement(channel, 'title').text = 'The Brand Identity - Features'
        ET.SubElement(channel, 'link').text = self.features_url
        ET.SubElement(channel, 'description').text = 'Latest features from The Brand Identity - Graphic Design\'s Greatest'
        ET.SubElement(channel, 'language').text = 'en-us'
        ET.SubElement(channel, 'lastBuildDate').text = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S %z')
        ET.SubElement(channel, 'generator').text = 'The Brand Identity RSS Generator'
        
        # Agregar artículos
        for article in articles:
            item = ET.SubElement(channel, 'item')
            
            ET.SubElement(item, 'title').text = article['title']
            ET.SubElement(item, 'link').text = article['url']
            ET.SubElement(item, 'description').text = article['description']
            ET.SubElement(item, 'guid', isPermaLink='true').text = article['guid']
            ET.SubElement(item, 'pubDate').text = article['pub_date'].strftime('%a, %d %b %Y %H:%M:%S %z')
            
            if article['image_url']:
                ET.SubElement(item, 'media:thumbnail', url=article['image_url'])
        
        return ET.tostring(rss, encoding='unicode', method='xml')
    
    def save_rss(self, rss_content, filename='feed.xml'):
        """Guarda el RSS a archivo"""
        # Agregar declaración XML y formatear
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
        formatted_rss = xml_declaration + rss_content
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(formatted_rss)
        
        print(f"RSS saved to {filename}")
        
    def save_metadata(self, articles, filename='metadata.json'):
        """Guarda metadatos para debugging"""
        metadata = {
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'articles_count': len(articles),
            'articles': []
        }
        
        for article in articles:
            metadata['articles'].append({
                'title': article['title'],
                'url': article['url'],
                'pub_date': article['pub_date'].isoformat()
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        print(f"Metadata saved to {filename}")
    
    def run(self):
        """Ejecuta el generador completo"""
        print("=== The Brand Identity RSS Generator ===")
        print(f"Starting at {datetime.now()}")
        
        articles = self.fetch_articles()
        
        if not articles:
            print("No articles found! Check the scraping logic.")
            return False
            
        print(f"Processing {len(articles)} articles...")
        
        rss_content = self.generate_rss(articles)
        self.save_rss(rss_content)
        self.save_metadata(articles)
        
        print("RSS generation completed successfully!")
        return True

if __name__ == "__main__":
    generator = TheBrandIdentityRSS()
    success = generator.run()
    
    if not success:
        exit(1)
