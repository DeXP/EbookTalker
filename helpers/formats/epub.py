import zipfile
import xml.etree.ElementTree as ET
import html
import os
import re
from collections import defaultdict

def normalize_path(path):
    """Normalize path to use forward slashes (as used in ZIP archives)"""
    return path.replace('\\', '/')

def parse_author_name(full_name):
    """Parse author name into components using regex patterns"""
    if not full_name:
        return {'full': None, 'first': None, 'middle': None, 'last': None}
    
    patterns = [
        r'^(?P<last>[^,]+),\s*(?P<first>\w+)(?:\s+(?P<middle>\w+))?$',
        r'^(?P<first>\w+)\s+(?P<middle>\w+\s)?(?P<last>\w+)$',
        r'^(?P<first>\w+)\s+(?P<last>\w+)$',
        r'^(?P<last>\w+)$'
    ]
    
    for pattern in patterns:
        match = re.match(pattern, full_name.strip(), re.UNICODE)
        if match:
            groups = match.groupdict()
            return {
                'full': full_name.strip(),
                'first': groups.get('first'),
                'middle': groups.get('middle', '').strip() or None,
                'last': groups.get('last')
            }
    
    return {
        'full': full_name.strip() if full_name else None,
        'first': None,
        'middle': None,
        'last': None
    }

def extract_encoding(xml_bytes):
    """Extract encoding from XML declaration"""
    declaration_match = re.search(
        br'^<\?xml\s+version="[^"]+"\s+encoding="([^"]+)"',
        xml_bytes.split(b'\n')[0]
    )
    return declaration_match.group(1).decode('ascii').lower() if declaration_match else 'utf-8'

def get_toc_data(rootfile_xml, ns, epub, rootfile_dir):
    """Extract table of contents data with human-readable titles"""
    toc_items = {}
    rootfile_dir = normalize_path(rootfile_dir)
    
    # First try to find NCX file (EPUB 2 preferred format)
    ncx_item = None
    for item in rootfile_xml.findall('.//opf:item', ns):
        if item.attrib.get('media-type') == 'application/x-dtbncx+xml':
            ncx_item = item
            break
    
    if ncx_item is not None:  # Proper element existence check
        toc_path = normalize_path(os.path.join(rootfile_dir, ncx_item.attrib['href']))
        try:
            with epub.open(toc_path) as toc_file:
                toc_bytes = toc_file.read()
                toc_xml = ET.fromstring(toc_bytes.decode(extract_encoding(toc_bytes)))
                
                # Parse NCX format
                for nav_point in toc_xml.findall('.//{*}navPoint'):
                    text = nav_point.find('.//{*}text')
                    src = nav_point.find('.//{*}content')
                    if text is not None and src is not None and text.text:
                        toc_items[normalize_path(src.attrib['src'].split('#')[0])] = text.text.strip()
        except Exception as e:
            print(f"Warning: Could not process NCX TOC file: {str(e)}")
    else:
        # Fallback to toc.xhtml if NCX not found
        toc_item = None
        for item in rootfile_xml.findall('.//opf:item', ns):
            if item.attrib.get('id', '').lower() == 'toc':
                toc_item = item
                break
        
        if toc_item is not None:  # Proper element existence check
            toc_path = normalize_path(os.path.join(rootfile_dir, toc_item.attrib['href']))
            try:
                with epub.open(toc_path) as toc_file:
                    toc_bytes = toc_file.read()
                    toc_xml = ET.fromstring(toc_bytes.decode(extract_encoding(toc_bytes)))
                    
                    # Parse NAV format (EPUB 3)
                    for li in toc_xml.findall('.//{*}li', ns):
                        a = li.find('{*}a')
                        if a is not None and 'href' in a.attrib and a.text:
                            toc_items[normalize_path(a.attrib['href'].split('#')[0])] = a.text.strip()
            except Exception as e:
                print(f"Warning: Could not process TOC file: {str(e)}")
    
    return toc_items

def get_xml_text(element, xpath, ns):
    """Helper to safely get text from XML element"""
    elem = element.find(xpath, ns)
    return elem.text if elem is not None and elem.text else None

def find_cover_image(epub, rootfile_xml, rootfile_dir, ns):
    """Try to locate and extract the cover image from the EPUB"""
    cover_id = None
    for meta in rootfile_xml.findall('.//opf:meta', ns):
        if meta.attrib.get('name', '').lower() == 'cover':
            cover_id = meta.attrib.get('content')
            break
    
    if not cover_id:
        common_covers = ['cover.jpg', 'cover.jpeg', 'cover.png', 'cover.gif']
        for item in rootfile_xml.findall('.//opf:item', ns):
            if any(item.attrib['href'].lower().endswith(ext) for ext in common_covers):
                cover_id = item.attrib['id']
                break
    
    if cover_id:
        for item in rootfile_xml.findall('.//opf:item', ns):
            if item.attrib.get('id') == cover_id:
                cover_path = normalize_path(os.path.join(rootfile_dir, item.attrib['href']))
                try:
                    with epub.open(cover_path) as cover_file:
                        return cover_file.read()
                except Exception:
                    continue
    
    return None

def process_content(content_bytes, encoding):
    """Process content file and return all text content excluding title tags"""
    try:
        content_xml = ET.fromstring(content_bytes.decode(encoding))
    except UnicodeDecodeError:
        content_xml = ET.fromstring(content_bytes.decode('utf-8'))
    
    text_content = []
    title = None
    
    # Get title from <title> tag if it exists
    title_elem = content_xml.find('.//{*}title')
    if title_elem is not None and title_elem.text:
        title = html.unescape(title_elem.text.strip())
    
    # Collect all other text content
    for elem in content_xml.iter():
        if elem.tag.endswith('}title'):
            continue
            
        if elem.text and elem.text.strip():
            text = html.unescape(elem.text.strip())
            text = re.sub(r'\s+', ' ', text)
            text_content.append(text)
        if elem.tail and elem.tail.strip():
            tail = html.unescape(elem.tail.strip())
            tail = re.sub(r'\s+', ' ', tail)
            text_content.append(tail)
    
    return title, text_content

def epub_to_sections(epub_path):
    """
    Convert an EPUB file to structured sections.
    
    Args:
        epub_path: Path to the EPUB file
    
    Returns:
        tuple: (result_dict, cover_image_bytes)
        - result_dict: Dictionary containing book data and sections
        - cover_image_bytes: Bytes of cover image if found, else None
    """
    result = {
        'title': None,
        'language': None,
        'encoding': 'utf-8',
        'author': None,  # Full author name
        'author_first': None,
        'author_middle': None,
        'author_last': None,
        'sections': []
    }
    
    cover_image = None
    
    with zipfile.ZipFile(epub_path, 'r') as epub:
        # Parse container to find rootfile
        with epub.open('META-INF/container.xml') as container_file:
            container = ET.fromstring(container_file.read())
        
        rootfile_path = normalize_path(container.find('.//{*}rootfile').attrib['full-path'])
        rootfile_dir = normalize_path(os.path.dirname(rootfile_path))
        
        # Read rootfile
        with epub.open(rootfile_path) as rootfile:
            rootfile_bytes = rootfile.read()
            encoding = extract_encoding(rootfile_bytes)
            try:
                rootfile_xml = ET.fromstring(rootfile_bytes.decode(encoding))
            except UnicodeDecodeError:
                rootfile_xml = ET.fromstring(rootfile_bytes.decode('utf-8'))
                encoding = 'utf-8'
        
        ns = {
            'opf': 'http://www.idpf.org/2007/opf',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'xhtml': 'http://www.w3.org/1999/xhtml'
        }
        
        # Extract metadata
        result['title'] = get_xml_text(rootfile_xml, './/dc:title', ns)
        result['language'] = get_xml_text(rootfile_xml, './/dc:language', ns)
        result['encoding'] = encoding
        
        # Extract author information
        creators = rootfile_xml.findall('.//dc:creator', ns)
        if creators and creators[0].text:
            author_data = parse_author_name(creators[0].text)
            result['author'] = author_data['full']
            result['author_first'] = author_data['first']
            result['author_middle'] = author_data['middle']
            result['author_last'] = author_data['last']
        
        # Find cover image
        cover_image = find_cover_image(epub, rootfile_xml, rootfile_dir, ns)
        
        # Get TOC data
        toc_data = get_toc_data(rootfile_xml, ns, epub, rootfile_dir)
        
        # Process all content files in spine order
        spine_items = rootfile_xml.findall('.//opf:itemref', ns)
        spine_order = {item.attrib['idref']: idx for idx, item in enumerate(spine_items)}
        
        content_items = []
        for item in rootfile_xml.findall('.//opf:item', ns):
            if (item.attrib.get('media-type') == 'application/xhtml+xml' and 
                not item.attrib.get('href', '').lower().endswith('toc.xhtml')):
                content_items.append({
                    'id': item.attrib['id'],
                    'href': normalize_path(item.attrib['href']),
                    'order': spine_order.get(item.attrib['id'], float('inf'))
                })
        
        content_items.sort(key=lambda x: x['order'])
        
        for item in content_items:
            content_path = normalize_path(os.path.join(rootfile_dir, item['href']))
            try:
                with epub.open(content_path) as content_file:
                    content_bytes = content_file.read()
                    content_encoding = extract_encoding(content_bytes)
                    
                    # Process content to get title and text
                    content_title, text_content = process_content(content_bytes, content_encoding)
                    
                    # Determine the best title
                    title = (toc_data.get(item['href']) or 
                            content_title or 
                            os.path.splitext(os.path.basename(item['href']))[0])
                    
                    if text_content:
                        result['sections'].append({
                            'title': title.strip() if title else "Untitled Section",
                            'text': text_content
                        })
            except Exception as e:
                print(f"Warning: Could not process {content_path}: {str(e)}")
    
    return result, cover_image

if __name__ == '__main__':
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python epub_to_txt.py <epub_file> [output_json_file]")
        sys.exit(1)
    
    epub_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        result, cover_image = epub_to_sections(epub_file)
        
        print("Book Information:")
        print(f"Title: {result.get('title')}")
        print(f"Author: {result.get('author')}")
        if result.get('author_first') or result.get('author_last'):
            print(f"Author Details: {result.get('author_first')} {result.get('author_middle') or ''} {result.get('author_last')}".strip())
        print(f"Language: {result.get('language')}")
        print(f"Encoding: {result.get('encoding')}")
        
        print(f"\nCover image found: {'Yes' if cover_image else 'No'}")
        print(f"\nFound {len(result['sections'])} sections/chapters")
        
        if cover_image:
            cover_ext = 'jpg'
            cover_path = os.path.splitext(epub_file)[0] + f'_cover.{cover_ext}'
            with open(cover_path, 'wb') as f:
                f.write(cover_image)
            print(f"Cover image saved to {cover_path}")
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nStructured data saved to {output_file}")
    except Exception as e:
        print(f"Error converting file: {str(e)}")
        sys.exit(1)