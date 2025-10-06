import xml.etree.ElementTree as ET

def sanitize(text):
    """Metni temizle, boşsa boş string döndür"""
    if text is None:
        return ""
    return str(text).replace("\n", "").replace("\r", "").strip()

def safe_split_component(component):
    """EDIFACT : split güvenli"""
    try:
        return component.split(":")[0], component.split(":")[1]
    except IndexError:
        return component, ""

edifact_message = """
orders example
"""

segments = [line.strip() for line in edifact_message.split("'") if line.strip()]

root = ET.Element("SCHEDULES")
schedules_el = ET.SubElement(root, "SCHEDULES")
schedule = ET.SubElement(schedules_el, "SCHEDULE")

ET.SubElement(schedule, "SUPP_SCHED_TYPE").text = "ORDERS"

for seg in segments:
    parts = seg.split("+")
    tag = parts[0]

    if tag == "NAD":
        party_qualifier = parts[1]
        party_id = sanitize(parts[2].split(":")[0])
        if party_qualifier == "SU":
            ET.SubElement(schedule, "VENDOR_NO").text = party_id
        elif party_qualifier == "BY":
            ET.SubElement(schedule, "BUYER_NO").text = party_id
        elif party_qualifier == "DP":
            ET.SubElement(schedule, "DELIVERY_PARTY_NO").text = party_id
            ET.SubElement(schedule, "EAN_LOCATION").text = party_id
        elif party_qualifier == "IV":
            ET.SubElement(schedule, "INVOICE_PARTY_NO").text = party_id

    elif tag == "BGM":
        ET.SubElement(schedule, "MESSAGE_ID").text = sanitize(parts[2])

    elif tag == "DTM":
        date_qualifier = parts[1].split(":")[0]
        date_value = parts[1].split(":")[1]
        formatted_date = f"{date_value[:4]}-{date_value[4:6]}-{date_value[6:]}T00:00:00"
        if date_qualifier == "137":
            ET.SubElement(schedule, "VALID_FROM").text = formatted_date
        elif date_qualifier == "2":
            ET.SubElement(schedule, "VALID_UNTIL").text = formatted_date

    elif tag == "RFF":
        ET.SubElement(schedule, "SUPPLIER_REF").text = sanitize(parts[1].split(":")[1])

article_lines_el = ET.SubElement(schedule, "ARTICLE_LINES")
demand_lines_el = ET.SubElement(schedule, "DEMAND_LINES")
current_article_line = None
last_demand_line = None
schedule_no = 1
line_type_id = "1"

for seg in segments:
    parts = seg.split("+")
    tag = parts[0]

    schedule_no_str = str(schedule_no)

    if tag == "LIN":
        # ARTICLE_LINE
        current_article_line = ET.SubElement(article_lines_el, "ARTICLE_LINE")
        ean_code = sanitize(parts[3].split(":")[0]) if len(parts) > 3 and ":" in parts[3] else ""
        ET.SubElement(current_article_line, "EAN_CODE").text = ean_code
        ET.SubElement(current_article_line, "CALL_OFF_NO").text = sanitize(schedule.findtext("MESSAGE_ID", ""))
        ET.SubElement(current_article_line, "LAST_RECEIPT_DATE").text = sanitize(schedule.findtext("VALID_UNTIL", ""))
        ET.SubElement(current_article_line, "SCHEDULE_NO").text = schedule_no_str

        # DEMAND_LINE
        current_demand_line = ET.SubElement(demand_lines_el, "SCHEDULE_LINE")
        ET.SubElement(current_demand_line, "PART_NO").text = ""  
        ET.SubElement(current_demand_line, "LINE_TYPE_ID").text = line_type_id
        ET.SubElement(current_demand_line, "DOCK_CODE").text = sanitize(schedule.findtext("EAN_LOCATION", ""))
        ET.SubElement(current_demand_line, "SCHEDULE_NO").text = schedule_no_str
        ET.SubElement(current_demand_line, "QUANTITY_DUE").text = "0" 
        ET.SubElement(current_demand_line, "DELIVERY_DUE_DATE").text = sanitize(schedule.findtext("VALID_UNTIL", ""))
        ET.SubElement(current_demand_line, "CUSTOMER_PO_NO").text = sanitize(schedule.findtext("MESSAGE_ID", ""))
        ET.SubElement(current_demand_line, "TO_DATE").text = sanitize(schedule.findtext("VALID_UNTIL", ""))
        last_demand_line = current_demand_line
        schedule_no += 1

    elif tag == "PIA" and current_article_line is not None and last_demand_line is not None:
        if len(parts) > 2 and ":" in parts[2]:
            code, qual = safe_split_component(parts[2])
            if qual == "BP":
                ET.SubElement(current_article_line, "PART_NO").text = sanitize(code)
                pn = last_demand_line.find("PART_NO")
                if pn is not None:
                    pn.text = sanitize(code)

    elif tag == "IMD" and current_article_line is not None:
        desc = sanitize(parts[3].replace(":::", "")) if len(parts) > 3 else ""
        ET.SubElement(current_article_line, "DESCRIPTION").text = desc

    elif tag == "QTY" and current_article_line is not None and last_demand_line is not None:
        qty_val = "0"
        try:
            qty_val = sanitize(parts[1].split(":")[1])
        except Exception:
            qty_val = "0"
        ET.SubElement(current_article_line, "LAST_RECEIPT_QTY").text = qty_val
        qd = last_demand_line.find("QUANTITY_DUE")
        if qd is not None:
            qd.text = qty_val
        print("quantity atandı")

    elif tag == "PRI" and current_article_line is not None:
        price_val = "0"
        try:
            price_val = sanitize(parts[1].split(":")[1])
        except Exception:
            price_val = "0"
        ET.SubElement(current_article_line, "UNIT_PRICE").text = price_val
        print("price atandı")

    
    
def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent(child, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

indent(root)

tree = ET.ElementTree(root)
tree.write("Documents/output.xml", encoding="ISO-8859-1", xml_declaration=True)

print("XML dosyası başarıyla oluşturuldu: output.xml")
