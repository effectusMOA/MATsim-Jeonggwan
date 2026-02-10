import xml.etree.ElementTree as ET
import sys

def fix_network(input_file, output_file):
    print(f"Parsing {input_file}...")
    tree = ET.parse(input_file)
    root = tree.getroot()

    links_element = root.find('links')
    if links_element is None:
        print("No 'links' element found.")
        return

    seen_ids = set()
    to_remove = []

    print("Checking for duplicates...")
    for link in links_element.findall('link'):
        link_id = link.get('id')
        if link_id in seen_ids:
            print(f"Duplicate link found: {link_id}")
            to_remove.append(link)
        else:
            seen_ids.add(link_id)

    print(f"Found {len(to_remove)} duplicates.")
    
    for link in to_remove:
        links_element.remove(link)

    print(f"Writing fixed network to {output_file}...")
    
    # Write the tree to a file
    tree.write(output_file, encoding='UTF-8', xml_declaration=True)
    
    # Prepend DOCTYPE manually as ElementTree doesn't support it easily
    doctype = '<!DOCTYPE network SYSTEM "http://www.matsim.org/files/dtd/network_v2.dtd">\n'
    
    with open(output_file, 'r+', encoding='UTF-8') as f:
        content = f.read()
        f.seek(0, 0)
        # Find the end of the XML declaration
        xml_decl_end = content.find('?>') + 2
        if xml_decl_end > 1:
            final_content = content[:xml_decl_end] + '\n' + doctype + content[xml_decl_end:].lstrip()
        else:
            final_content = doctype + content
        f.write(final_content)
        f.truncate()
        
    print("Done.")

if __name__ == "__main__":
    input_path = "input/jeonggwan-network.xml"
    output_path = "input/jeonggwan-network-fixed.xml"
    fix_network(input_path, output_path)
