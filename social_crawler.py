import scrapy
from scrapy.crawler import CrawlerProcess
from urllib.parse import urljoin, urlparse, parse_qs, unquote


class DuckDuckGoSpider(scrapy.Spider):
    name = "global_osint_spider"
    seen_links = set()
    found_profiles = []

    def __init__(self, name_to_search, max_pages=2, *args, **kwargs):
        super(DuckDuckGoSpider, self).__init__(*args, **kwargs)
        self.name_to_search = name_to_search.replace(" ", "+")
        self.search_name_clean = name_to_search.lower()
        self.max_pages = max_pages

        self.sources = {
            "Web_Broad": f"https://duckduckgo.com/html/?q={self.name_to_search}",
            "Web_Exact": f"https://duckduckgo.com/html/?q=%22{self.name_to_search}%22",
            "Image_Search": f"https://www.bing.com/images/search?q={self.name_to_search}"
        }

    def start_requests(self):
        # התחפושת של הדפדפן - נשתמש בה רק איפה שצריך
        chrome_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36'}

        for label, url in self.sources.items():
            print(f"🌐 יוצר קשר עם מנוע חיפוש: {label}...")
            if label == "Image_Search":
                # בינג דורש את התחפושת כדי לא לחסום
                yield scrapy.Request(url, meta={'source_label': label, 'page_num': 1}, headers=chrome_headers)
            else:
                # DuckDuckGo חייב לבוא טבעי, אחרת הוא חוסם
                yield scrapy.Request(url, meta={'source_label': label, 'page_num': 1})

    def parse(self, response, **kwargs):
        source_label = response.meta.get('source_label', 'Unknown')
        current_page = response.meta.get('page_num', 1)

        print(f"✅ התקבלה תשובה מ-{source_label} (עמוד {current_page})")

        # ==========================================
        # 1. מנוע חיפוש תמונות (Bing)
        # ==========================================
        if source_label == "Image_Search":
            images = response.css("img::attr(src), img::attr(data-src)").getall()
            found_count = 0
            for img_src in set(images):
                if img_src and img_src.startswith("http"):
                    DuckDuckGoSpider.found_profiles.append({
                        "title": f"Direct Image Search Result ({self.search_name_clean})",
                        "link": response.url,
                        "img": img_src
                    })
                    found_count += 1

            print(f"   📸 נשאבו {found_count} תמונות ישירות ממנוע התמונות!")
            return

            # ==========================================
        # 2. מנועי טקסט ואתרים (DuckDuckGo)
        # ==========================================
        results = response.css("div.result")
        print(f"   📄 נמצאו {len(results)} אתרים ב-{source_label}. נכנס לחפש בהם תמונות...")

        # התחפושת לאתרים הפנימיים
        chrome_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36'}

        for result in results:
            a_tag = result.css("a.result__a")
            if not a_tag: continue

            title = ' '.join(a_tag.css("*::text").getall()).strip()
            link = a_tag.attrib.get("href")
            if not link:
                continue

            parsed = urlparse(link)
            query = parse_qs(parsed.query)
            link_clean = unquote(query.get("uddg", [link])[0]) if "uddg" in query else link

            if link_clean in self.seen_links:
                continue

            self.seen_links.add(link_clean)

            name_in_title = self.search_name_clean in title.lower()

            if name_in_title:
                DuckDuckGoSpider.found_profiles.append({
                    "title": title,
                    "link": link_clean,
                    "img": None
                })

            # שולחים את הבוט לתוך האתר האמיתי - עם התחפושת!
            yield scrapy.Request(
                url=link_clean,
                callback=self.parse_inside_page,
                meta={'title': title, 'link': link_clean, 'name_in_title': name_in_title,
                      'handle_httpstatus_all': True},
                headers=chrome_headers
            )

        next_page = response.css("a.result--more__btn::attr(href)").get()
        if next_page and current_page < self.max_pages:
            yield response.follow(
                urljoin(response.url, next_page),
                callback=self.parse,
                meta={'source_label': source_label, 'page_num': current_page + 1}
            )

    def parse_inside_page(self, response):
        title = response.meta['title']
        link = response.meta['link']
        name_in_title = response.meta['name_in_title']

        if response.status != 200:
            return

        page_text = " ".join(response.css("body *::text").getall()).lower()
        name_in_text = self.search_name_clean in page_text

        if not (name_in_title or name_in_text):
            return

        if name_in_text and not name_in_title:
            DuckDuckGoSpider.found_profiles.append({
                "title": title,
                "link": link,
                "img": None
            })

        images = response.css("img::attr(src), img::attr(data-src), img::attr(data-original)").getall()
        unique_images = set(images)

        for img_src in unique_images:
            if not img_src: continue
            full_img_url = response.urljoin(img_src)
            if full_img_url.startswith("http"):
                DuckDuckGoSpider.found_profiles.append({
                    "title": title,
                    "link": link,
                    "img": full_img_url
                })


# בתוך קובץ crawler.py - שנה רק את ה-CrawlerManager:

class CrawlerManager:
    @staticmethod
    def run_crawler(name, filename="results.json"):
        custom_settings = {
            "LOG_LEVEL": "ERROR",
            "DOWNLOAD_DELAY": 0.5,
            "FEEDS": {filename: {"format": "json", "overwrite": True}}, # שומר לקובץ
        }
        process = CrawlerProcess(settings=custom_settings)
        process.crawl(DuckDuckGoSpider, name_to_search=name)
        process.start()