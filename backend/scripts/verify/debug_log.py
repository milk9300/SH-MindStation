import re
try:
    with open('test_api_out.log', 'r', encoding='utf-16le') as f:
        html = f.read()
        match = re.search(r'<pre class="exception_value">(.*?)</pre>', html, re.DOTALL)
        if match:
            print("EXCEPTION VALUE:", match.group(1).strip())
        else:
            print("No <pre class=\"exception_value\"> found. Attempting to parse traceback...")
            match2 = re.search(r'<textarea id="traceback_area".*?>(.*?)</textarea>', html, re.DOTALL)
            if match2:
                print(match2.group(1)[:2000])
            else:
                print("Could not find standard django exception tags.")
except Exception as e:
    print(e)
