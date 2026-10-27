"""Check every generated page's relative links and sitemap targets offline."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse,unquote
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]/'dist'

class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.base='./';self.links=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='base':self.base=attrs['href']
        if tag=='a' and attrs.get('href'):self.links.append(attrs['href'])

count=0
for file in ROOT.rglob('*.html'):
    parser=Links();parser.feed(file.read_text())
    base=ROOT if urlparse(parser.base).scheme else (file.parent/parser.base).resolve()
    for href in parser.links:
        if urlparse(href).scheme or href.startswith('#'):continue
        target=(base/unquote(urlparse(href).path)).resolve()
        assert target.is_file() or (target/'index.html').is_file(),(file,href,target)
    count+=1
if (ROOT/'sitemap.xml').exists():
    tree=ET.parse(ROOT/'sitemap.xml')
    assert len(tree.getroot())>=count-1
print(f'All relative links valid across {count} HTML pages')
