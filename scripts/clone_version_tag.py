import sys
import copy
from copy import deepcopy

if len(sys.argv) != 4:
    print("Usage: xxx.py <old_version> <new_version> <filename>")
    exit(1)

version_to_copy = sys.argv[1]
new_version = sys.argv[2]
filename = sys.argv[3]

def use_lxml():
    import lxml.etree as ET
    root = ET.parse(filename).getroot()
    [version_to_copy_element] = root.xpath('//version[@number="%s"]' % version_to_copy)
    new_version_element = deepcopy(version_to_copy_element)
    new_version_element.attrib['number'] = new_version
    version_to_copy_element.addprevious(new_version_element)
    #print(ET.tostring(root, encoding='utf-8'))
    ET.ElementTree(root).write(filename)

def use_bs():
    from bs4 import BeautifulSoup
    with open(filename) as fp:
        soup = BeautifulSoup(fp, 'lxml')
        version_to_copy_element = soup.find('version', number='%s' % version_to_copy)
        #version_to_copy_tag = soup.select('version[number="%s"]' % version_to_copy )
        new_version_element = copy.copy(version_to_copy_element)
        new_version_element['number'] = new_version
        version_to_copy_element.insert_before(new_version_element)
        #print(soup)
        #print(soup.prettify())

use_lxml()