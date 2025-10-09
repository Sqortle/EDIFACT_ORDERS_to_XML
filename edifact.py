import xml.etree.ElementTree as ET

class XMLConverter():

    def __init__(self, edifact_message):
        self.edifact_message = edifact_message
        self.segments_class = SegmentsClass(self)
        self.root = self.convert(edifact_message)

    def sanitize(self, text):
        if text is None:
            return ""
        return str(text).replace("\n", "").replace("\r", "").strip()

    def safe_split_component(self, component):
        try:
            return component.split(":")[0], component.split(":")[1]
        except IndexError:
            return component, ""
        
    def convert(self, edifact_message):
        segments = [line.strip() for line in edifact_message.split("'") if line.strip()]

        root = ET.Element("SCHEDULES")
        schedules_el = ET.SubElement(root, "SCHEDULES")
        schedule = ET.SubElement(schedules_el, "SCHEDULE")

        ET.SubElement(schedule, "SUPP_SCHED_TYPE").text = "ORDERS"

        for seg in segments:
            parts = seg.split("+")
            tag = parts[0]

            if tag == "NAD":
                self.segments_class.NADfunction(schedule, parts)
            elif tag == "BGM":
                self.segments_class.BGMfunction(schedule, parts)
            elif tag == "DTM":
                self.segments_class.DTMfunction(schedule, parts)
            elif tag == "RFF":
                self.segments_class.RFFfunction(schedule, parts)

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
                current_article_line, last_demand_line = self.segments_class.LINfunction(schedule, parts, article_lines_el, demand_lines_el, schedule_no_str, line_type_id)
                schedule_no += 1
            elif tag == "PIA" and current_article_line is not None and last_demand_line is not None:
                self.segments_class.PIAfunction(parts, current_article_line, last_demand_line)
            elif tag == "IMD" and current_article_line is not None:
                self.segments_class.IMDfunction(parts, current_article_line)
            elif tag == "QTY" and current_article_line is not None and last_demand_line is not None:
                self.segments_class.QTYfunction(parts, current_article_line, last_demand_line)
            elif tag == "PRI" and current_article_line is not None:
                self.segments_class.PRIfunction(parts, current_article_line)

        return root

    def indent(self, elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            for child in elem:
                self.indent(child, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i


class SegmentsClass:

    def __init__(self, converter):
        self.converter = converter

    def NADfunction(self, schedule, parts):
        party_qualifier = parts[1]
        party_id = self.converter.sanitize(parts[2].split(":")[0])
        if party_qualifier == "SU":
            ET.SubElement(schedule, "VENDOR_NO").text = party_id
        elif party_qualifier == "BY":
            ET.SubElement(schedule, "BUYER_NO").text = party_id
        elif party_qualifier == "DP":
            ET.SubElement(schedule, "DELIVERY_PARTY_NO").text = party_id
            ET.SubElement(schedule, "EAN_LOCATION").text = party_id
        elif party_qualifier == "IV":
            ET.SubElement(schedule, "INVOICE_PARTY_NO").text = party_id

    def BGMfunction(self, schedule, parts):
        ET.SubElement(schedule, "MESSAGE_ID").text = self.converter.sanitize(parts[2])

    def DTMfunction(self, schedule, parts):
        date_qualifier = parts[1].split(":")[0]
        date_value = parts[1].split(":")[1]
        formatted_date = f"{date_value[:4]}-{date_value[4:6]}-{date_value[6:]}T00:00:00"
        if date_qualifier == "137":
            ET.SubElement(schedule, "VALID_FROM").text = formatted_date
        elif date_qualifier == "2":
            ET.SubElement(schedule, "VALID_UNTIL").text = formatted_date

    def RFFfunction(self, schedule, parts):
        ET.SubElement(schedule, "SUPPLIER_REF").text = self.converter.sanitize(parts[1].split(":")[1])

    def LINfunction(self, schedule, parts, article_lines_el, demand_lines_el, schedule_no_str, line_type_id):
        current_article_line = ET.SubElement(article_lines_el, "ARTICLE_LINE")
        ean_code = self.converter.sanitize(parts[3].split(":")[0]) if len(parts) > 3 and ":" in parts[3] else ""
        ET.SubElement(current_article_line, "EAN_CODE").text = ean_code
        ET.SubElement(current_article_line, "CALL_OFF_NO").text = self.converter.sanitize(schedule.findtext("MESSAGE_ID", ""))
        ET.SubElement(current_article_line, "LAST_RECEIPT_DATE").text = self.converter.sanitize(schedule.findtext("VALID_UNTIL", ""))
        ET.SubElement(current_article_line, "SCHEDULE_NO").text = schedule_no_str

        current_demand_line = ET.SubElement(demand_lines_el, "SCHEDULE_LINE")
        ET.SubElement(current_demand_line, "PART_NO").text = ""  
        ET.SubElement(current_demand_line, "LINE_TYPE_ID").text = line_type_id
        ET.SubElement(current_demand_line, "DOCK_CODE").text = self.converter.sanitize(schedule.findtext("EAN_LOCATION", ""))
        ET.SubElement(current_demand_line, "SCHEDULE_NO").text = schedule_no_str
        ET.SubElement(current_demand_line, "QUANTITY_DUE").text = "0" 
        ET.SubElement(current_demand_line, "DELIVERY_DUE_DATE").text = self.converter.sanitize(schedule.findtext("VALID_UNTIL", ""))
        ET.SubElement(current_demand_line, "CUSTOMER_PO_NO").text = self.converter.sanitize(schedule.findtext("MESSAGE_ID", ""))
        ET.SubElement(current_demand_line, "TO_DATE").text = self.converter.sanitize(schedule.findtext("VALID_UNTIL", ""))
        return current_article_line, current_demand_line

    def PIAfunction(self, parts, current_article_line, last_demand_line):
        if len(parts) > 2 and ":" in parts[2]:
            code, qual = self.converter.safe_split_component(parts[2])
            if qual == "BP":
                ET.SubElement(current_article_line, "PART_NO").text = self.converter.sanitize(code)
                pn = last_demand_line.find("PART_NO")
                if pn is not None:
                    pn.text = self.converter.sanitize(code)

    def IMDfunction(self, parts, current_article_line):
        desc = self.converter.sanitize(parts[3].replace(":::", "")) if len(parts) > 3 else ""
        ET.SubElement(current_article_line, "DESCRIPTION").text = desc

    def QTYfunction(self, parts, current_article_line, last_demand_line):
        qty_val = "0"
        try:
            qty_val = self.converter.sanitize(parts[1].split(":")[1])
        except Exception:
            qty_val = "0"
        ET.SubElement(current_article_line, "LAST_RECEIPT_QTY").text = qty_val
        qd = last_demand_line.find("QUANTITY_DUE")
        if qd is not None:
            qd.text = qty_val

    def PRIfunction(self, parts, current_article_line):
        price_val = "0"
        try:
            price_val = self.converter.sanitize(parts[1].split(":")[1])
        except Exception:
            price_val = "0"
        ET.SubElement(current_article_line, "UNIT_PRICE").text = price_val


edifact_message = """
    D96A orders 
    """

convert = XMLConverter(edifact_message)
convert.indent(convert.root)
tree = ET.ElementTree(convert.root)
tree.write("Documents/output.xml", encoding="ISO-8859-1", xml_declaration=True)
