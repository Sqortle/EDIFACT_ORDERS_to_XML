import xml.etree.ElementTree as ET

# EDIFACT mesajı
edifact_message = """
UNA:+.? '
UNB+UNOC:3+TURKEYMAPGLN:14+8690524000017:14+20250901:1245+I175671990319++++++1'
UNH+I175671990319+ORDERS:D:96A:UN:EAN008'
BGM+220+633035685+9'
DTM+137:20250901:102'
DTM+2:20250905:102'
NAD+SU+8690524000017::9'
RFF+API:035646'
NAD+BY+0000000003602::9'
NAD+DP+0000000003602::9'
NAD+IV+9044444083000::9'
LIN+1++8690515124272:EN'
PIA+1+00066340:BP'
IMD+B++:::OLIPS MENTOL OKALIPTUS12KT 24S'
QTY+21:288:PCE'
PRI+AAA:9.41'
LIN+2++8690515124273:EN'
PIA+1+00066341:BP'
IMD+B++:::OLIPS MENTOL NANE12KT 24S'
QTY+21:100:PCE'
PRI+AAA:8.90'
UNS+S'
UNT+27+I175671990319'
UNZ+1+I175671990319'

"""

segments = [line.strip() for line in edifact_message.split("'") if line.strip()]

root = ET.Element("SCHEDULES")
schedules_el = ET.SubElement(root, "SCHEDULES")
schedule = ET.SubElement(schedules_el, "SCHEDULE")

current_article_line = None

ET.SubElement(schedule, "SUPP_SCHED_TYPE").text = "ORDERS"

ean_code = None
pia_bp = None
description = None
qty = None
price = None
schedule_no = "1"
line_type_id = "1"

for seg in segments:
    parts = seg.split("+")
    tag = parts[0]

    if tag == "NAD":
        party_qualifier = parts[1]
        party_id = parts[2].split(":")[0]
        if party_qualifier == "SU":
            ET.SubElement(schedule, "VENDOR_NO").text = party_id
        elif party_qualifier == "BY":
            ET.SubElement(schedule, "BUYER_NO").text = party_id
        elif party_qualifier == "DP":
            ET.SubElement(schedule, "DELIVERY_PARTY_NO").text = party_id
            ET.SubElement(schedule, "EAN_LOCATION").text = parts[2].split(":")[0]
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
        print("ALI segmentinde")

    elif tag == "RFF":
        ET.SubElement(schedule, "SUPPLIER_REF").text = parts[1].split(":")[1]

        

article_lines = ET.SubElement(schedule, "ARTICLE_LINES")
demand_lines_el = ET.SubElement(schedule, "DEMAND_LINES")

current_article_line = None

for seg in segments:
    parts = seg.split("+")
    tag = parts[0]

    if tag == "LIN":
        
        current_article_line = ET.SubElement(article_lines, "ARTICLE_LINE")

        
        ean_code = ""
        if len(parts) > 3 and ":" in parts[3]:
            ean_code = parts[3].split(":")[0]
        ET.SubElement(current_article_line, "EAN_CODE").text = ean_code

        
        ET.SubElement(current_article_line, "CALL_OFF_NO").text = schedule.find("MESSAGE_ID").text if schedule.find("MESSAGE_ID") is not None else ""
        ET.SubElement(current_article_line, "LAST_RECEIPT_DATE").text = schedule.find("VALID_UNTIL").text if schedule.find("VALID_UNTIL") is not None else ""
        ET.SubElement(current_article_line, "SCHEDULE_NO").text = schedule_no

        
        current_demand_line = ET.SubElement(demand_lines_el, "SCHEDULE_LINE")
        
        ET.SubElement(current_demand_line, "PART_NO").text = ""  
        ET.SubElement(current_demand_line, "LINE_TYPE_ID").text = line_type_id
        ET.SubElement(current_demand_line, "DOCK_CODE").text = schedule.find("EAN_LOCATION").text if schedule.find("EAN_LOCATION") is not None else ""
        ET.SubElement(current_demand_line, "SCHEDULE_NO").text = schedule_no
        ET.SubElement(current_demand_line, "QUANTITY_DUE").text = "0"   # PIA/QTY geldikçe güncellenecek
        ET.SubElement(current_demand_line, "DELIVERY_DUE_DATE").text = schedule.find("VALID_UNTIL").text if schedule.find("VALID_UNTIL") is not None else ""
        ET.SubElement(current_demand_line, "CUSTOMER_PO_NO").text = schedule.find("MESSAGE_ID").text if schedule.find("MESSAGE_ID") is not None else ""
        ET.SubElement(current_demand_line, "TO_DATE").text = schedule.find("VALID_UNTIL").text if schedule.find("VALID_UNTIL") is not None else ""
        
        last_demand_line = current_demand_line

    elif tag == "PIA" and current_article_line is not None:
        
        if len(parts) > 2 and ":" in parts[2]:
            code, qual = parts[2].split(":")[0], parts[2].split(":")[1]
            if qual == "BP":
                ET.SubElement(current_article_line, "PART_NO").text = code
                
                if last_demand_line is not None:
                    pn = last_demand_line.find("PART_NO")
                    if pn is not None:
                        pn.text = code

    elif tag == "IMD" and current_article_line is not None:
        
        desc = ""
        if len(parts) > 3:
            desc = parts[3].replace(":::", "")
        ET.SubElement(current_article_line, "DESCRIPTION").text = desc

    elif tag == "QTY" and current_article_line is not None:
        
        qty_val = "0"
        try:
            qty_val = parts[1].split(":")[1]
        except Exception:
            qty_val = "0"
        
        ET.SubElement(current_article_line, "LAST_RECEIPT_QTY").text = qty_val
        
        if last_demand_line is not None:
            qd = last_demand_line.find("QUANTITY_DUE")
            if qd is not None:
                qd.text = qty_val
        print("quantity atandı")

    elif tag == "PRI" and current_article_line is not None:
        price_val = "0"
        try:
            price_val = parts[1].split(":")[1]
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
