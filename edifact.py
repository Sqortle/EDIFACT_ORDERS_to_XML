import xml.etree.ElementTree as ET

edifact_message = """
EDIFACT ORDERS MESSAGE Example
"""

segments = [line.strip() for line in edifact_message.split("'") if line.strip()]

root = ET.Element("SCHEDULES")
schedules_el = ET.SubElement(root, "SCHEDULES")
schedule = ET.SubElement(schedules_el, "SCHEDULE")


EAN_LOCATION = "0000000003602"
DOCK_CODE = "0000000003602"

current_article_line = None

ET.SubElement(schedule, "SUPP_SCHED_TYPE").text = "PLAN"

ean_code = None
pia_bp = None
description = None
qty = None
price = None

for seg in segments:
    parts = seg.split("+")
    tag = parts[0]

    if tag == "UNB":
        ET.SubElement(schedule, "SUPP_SCHED_TYPE").text = parts[2].split(":")[0]

    elif tag == "NAD":
        party_qualifier = parts[1]
        party_id = parts[2].split(":")[0]
        if party_qualifier == "SU":
            ET.SubElement(schedule, "VENDOR_NO").text = party_id
        elif party_qualifier == "BY":
            ET.SubElement(schedule, "BUYER_NO").text = party_id
        elif party_qualifier == "DP":
            ET.SubElement(schedule, "DELIVERY_PARTY_NO").text = party_id
        elif party_qualifier == "IV":
            ET.SubElement(schedule, "INVOICE_PARTY_NO").text = party_id

    elif tag == "BGM":
        ET.SubElement(schedule, "MESSAGE_ID").text = parts[2]
  

    elif tag == "DTM":
        date_qualifier = parts[1].split(":")[0]
        date_value = parts[1].split(":")[1]
        formatted_date = f"{date_value[:4]}-{date_value[4:6]}-{date_value[6:]}T00:00:00"
        if date_qualifier == "137":
            ET.SubElement(schedule, "VALID_FROM").text = formatted_date
        elif date_qualifier == "2":
            ET.SubElement(schedule, "VALID_UNTIL").text = formatted_date
            

    elif tag == "ALI":
        print("in ALI")

    elif tag == "RFF":
        ET.SubElement(schedule, "SUPPLIER_REF").text = parts[1].split(":")[1]

    elif tag == "LIN":
        ean_code = parts[3].split(":")[0]
        
        ET.SubElement(schedule, "EAN_LOCATION").text = EAN_LOCATION

    elif tag == "PIA":
        if parts[2].split(":")[1] == "BP":
            pia_bp = parts[2].split(":")[0]

    elif tag == "IMD":
        description = parts[3].replace(":::", "")
        

    elif tag == "QTY":
        try:
            qty = parts[1].split(":")[1]
            print("quantity atandı")
        except IndexError:
            qty = "0"
        

    elif tag == "PRI":
        try:
            price = parts[1].split(":")[1]
            print("price atandı")
        except IndexError:
            price = "0"
        


article_lines = ET.SubElement(schedule, "ARTICLE_LINES")
current_article_line = ET.SubElement(article_lines, "ARTICLE_LINE")
ET.SubElement(current_article_line, "CALL_OFF_NO").text = schedule.find("MESSAGE_ID").text
ET.SubElement(current_article_line, "SCHEDULE_NO").text = "1"
ET.SubElement(current_article_line, "LAST_RECEIPT_DATE").text = schedule.find("VALID_UNTIL").text
ET.SubElement(current_article_line, "EAN_CODE").text = ean_code
ET.SubElement(current_article_line, "PART_NO").text = pia_bp
ET.SubElement(current_article_line, "DESCRIPTION").text = description
ET.SubElement(current_article_line, "LAST_RECEIPT_QTY").text = qty
ET.SubElement(current_article_line, "UNIT_PRICE").text = price

demand_lines_el = ET.SubElement(schedule, "DEMAND_LINES")
current_demand_line = ET.SubElement(demand_lines_el, "SCHEDULE_LINE")
ET.SubElement(current_demand_line, "PART_NO").text = current_article_line.find("PART_NO").text
ET.SubElement(current_demand_line, "LINE_TYPE_ID").text = "1"
ET.SubElement(current_demand_line, "DOCK_CODE").text = DOCK_CODE
ET.SubElement(current_demand_line, "QUANTITY_DUE").text = current_article_line.find("LAST_RECEIPT_QTY").text
ET.SubElement(current_demand_line, "DELIVERY_DUE_DATE").text = schedule.find("VALID_UNTIL").text
ET.SubElement(current_demand_line, "CUSTOMER_PO_NO").text = schedule.find("MESSAGE_ID").text
ET.SubElement(current_demand_line, "TO_DATE").text = schedule.find("VALID_UNTIL").text


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

print("Successful!")
