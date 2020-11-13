# Tutorial

In this tutorial, we will walk through how to extract statements from financial reports published by the city of Berkeley, California from two separate years. Download the PDFs from the city of Berkeley website and follow along.
```
git clone https://github.com/melvinw/cafr-parser
cd cafr-parser
curl -o berkeley-2019.pdf "https://www.cityofberkeley.info/uploadedFiles/Finance/Level_3_-_General/FY2019CAFRReport.pdf" 
curl -o berkeley-2010.pdf "https://www.cityofberkeley.info/uploadedFiles/Finance/Level_3_-_General/FY2010%20Berkeley%20CAFR%20Final.pdf"
```

# Basic Example

The Statement of Net Position in the 2019 report is formatted in a pretty standard way and is on page 56. Let's parse and transform into to a CSV so we can dump it into a spreadsheet or some other program to do some analysis. A value of `-` indicates the absence of data in a cell.
```
$ ./parse-cafr.py 2019.pdf 55 --format csv
<snip>
label,Governmental Activities,Business-Type Activities,Total,Rent Stabilization Board
Cash and investments,220581964.0,81956522.0,302538486.0,6410679.0
Receivables (net of allowance for uncollectible),34086776.0,3771792.0,37858568.0,-
Prepaid items,485140.0,-,485140.0,-
Inventories,63974.0,-,63974.0,-
Internal balances,-10259094.0,10259094.0,-,-
Total current assets,244958760.0,95987408.0,340946168.0,6410679.0
<snip>
```

Add the `--format json` option to get a JSON-formatted assets. The `column_data` key-value pairs correspond to the fields of the CSV output (zero-indexed offset starting after the label field).
```
$ ./parse-cafr.py 2019.pdf 55 --format json
[
<snip>
    {
        "label": "Cash and investments",
        "column_data": {
            "Governmental Activities": 220581964.0,
            "Business-Type Activities": 81956522.0,
            "Total": 302538486.0,
            "Rent Stabilization Board": 6410679.0
        }
    },
    {
        "label": "Receivables (net of allowance for uncollectible)",
        "column_data": {
            "Governmental Activities": 34086776.0,
            "Business-Type Activities": 3771792.0,
            "Total": 37858568.0
        }
    },
    {
        "label": "Prepaid items",
        "column_data": {
            "Governmental Activities": 485140.0,
            "Total": 485140.0
        }
    },
    {
        "label": "Inventories",
        "column_data": {
            "Governmental Activities": 63974.0,
            "Total": 63974.0
        }
    },
    {
        "label": "Internal balances",
        "column_data": {
            "Governmental Activities": -10259094.0,
            "Business-Type Activities": 10259094.0
        }
    },
    {
        "label": "Total current assets",
        "column_data": {
            "Governmental Activities": 244958760.0,
            "Business-Type Activities": 95987408.0,
            "Total": 340946168.0,
            "Rent Stabilization Board": 6410679.0
        }
    },
<snip>
]
```

# Multi-Page Statements

The Statement of Activities in the 2019 report has an unfortunately long table that got split across pagse 58 and 59. You can concatenate the pages horizontally and translate the table to a CSV with the following by listing both pages on the command line, separated by a comma (or a dash).
```
$ ./parse-cafr.py 2019.pdf 57,58 --format csv
<snip>
Governmental activities:,-,-,-,-,-,-,-,-,-,-
General government,44836569.0,-5223724.0,4313273.0,75500.0,-,-35224072.0,-,-35224072.0,-,-
Public safety,133934428.0,-,11145339.0,2126511.0,-,-120662578.0,-,-120662578.0,-,-
Highways and streets,22244158.0,60748.0,1413973.0,405508.0,2145942.0,-18339483.0,-,-18339483.0,-,-
Health and welfare,35370732.0,-,1479103.0,13835779.0,-,-20055850.0,-,-20055850.0,-,-
Culture and recreation,52589539.0,-,2291989.0,124246.0,1217410.0,-48955894.0,-,-48955894.0,-,-
Community development and housing,27198932.0,147456.0,5165907.0,10465156.0,-,-11715325.0,-,-11715325.0,-,-
Economic development,5459482.0,-,463045.0,-,-,-4996437.0,-,-4996437.0,-,-
Interest on long-term debt,4970956.0,-,-,-,-,-4970950.0,-,-4970950.0,-,-
Total governmental activities,326604796.0,-5015520.0,26272629.0,27032700.0,3363352.0,-264920595.0,-,-264920595.0,-,-
<snip>
General Revenues:,-,-,-,-,-,-,-,-,-,-
Taxes:,-,-,-,-,-,-,-,-,-,-
Property taxes levied for general purposes,-,-,-,-,-,100258772.0,-,100258772.0,-,-
Property taxes levied for debt services,-,-,-,-,-,10173201.0,-,10173201.0,-,-
Property taxes levied for special purposes - i,-,-,-,-,-,-,-,-,-,-
Library,-,-,-,-,-,19697647.0,-,19697647.0,-,-
Parks,-,-,-,-,-,13386448.0,-,13386448.0,-,-
Paramedic,-,-,-,-,-,3050159.0,-,3050159.0,-,-
Fire,-,-,-,-,-,5044450.0,-,5044450.0,-,-
Sales taxes,-,-,-,-,-,20652090.0,-,20652090.0,-,-
Utility users taxes,-,-,-,-,-,13898172.0,-,13898172.0,-,-
Transient occupancy taxes,-,-,-,-,-,9855058.0,-,9855058.0,-,-
Business license tax,-,-,-,-,-,27740995.0,-,27740995.0,-,-
Other taxes,-,-,-,-,-,25008813.0,-,25008813.0,-,-
Total taxes,-,-,-,-,-,248765805.0,-,248765805.0,-,-
Other unrestricted state subventions,-,-,-,-,-,387181.0,-,387181.0,-,-
Contributions not restricted to specific programs,-,-,-,-,-,462614.0,-,462614.0,-,-
Investment earnings,-,-,-,-,-,10060124.0,2392270.0,12452394.0,-,-
Insurance reimbursement,-,-,-,-,-,17927255.0,-,17927255.0,-,-
Miscellaneous,-,-,-,-,-,2922834.0,-,2922834.0,-,-
Transfers:,-,-,-,-,-,-,-,-,-,-
Primary government,-,-,-,-,-,4816081.0,-4816681.0,-,-,-
Total general revenues and transfers,-,-,-,-,-,285342494.0,-2424411.0,282918083.0,-,-
Changes in net position,-,-,-,-,-,20421899.0,9571149.0,29993048.0,-,-156554.0
Net position - beginning as restated,-,-,-15.0,-,-,-123474344.0,167198824.0,43724480.0,-,-5190732.0
Net position - ending,-,-,-,-,-,-103052445.0,176769973.0,73717528.0,-,-5347286.0
<snip>
```

# Rotated Statements

The Statement of Net Position in the 2010 is on page 51 of the PDF. The statement is formatted in a standard way, but is presented sideways (a common occurrence for financial report statements) and will need to be rotated before any text can be extracted. You can do this by setting the `--rotate` option to rotate it clockwise.
```
$ ./parse-cafr.py 2010.pdf 50 --rotate 90 --format csv
<snip>
Governmenial ectivilies:,-,-,-,-,-,-,-,-,-,-
General governmenl $ 34 530366 $(4.943278) $ 2464243 $ 198482 S - § (26.924383) ¥ - S,-,-,-,-,-,-,-,-,-28924363.0,-
FPublic sefely,84403319.0,-,15341433.0,276942.0,-,-,-88784545.0,-,-68784945.0,-
Highways and streels,13718208.0,121846.0,2974062.0,4081391.0,-,8102721.0,138121.0,-,1318121.0,-
Health and wellfare,24082486.0,-,1387591.0,15554684.0,-,-,-7160211.0,-,-7160211.0,-
Culture and recreation,3457549.0,-,3037335.0,212561.0,-,-,-31325597.0,-,-31325597.0,-
Community development end housing,24133628.0,228096.0,2292171.0,11403944.0,-,-,-10685810.0,-,-10885810.0,-
L conomic developmant,5226694.0,-,480068.0,44352.0,-,-,-4702274.0,-,-4702274.0,-
interest on long-term debl,5117921.0,-,-,-,-,-,-5117921.0,-,-5117921.0,-
Totat governmental activitios 225788318 (4.593.336) 27956804 31772355 A.102.721,-,-,-,-,-,-,1153382999.0,-,-153362998.0,-
<snip>
{>enerel revenues:,-,-,-,-,-,-,-,-,-,-
Taxes:,-,-,-,-,-,-,-,-,-,-
Property laxes levied for generel purposes,-,-,-,-,-,-,50488138.0,-,50488138.0,-
Property taxes levied for debt service,-,-,-,-,-,-,8545702.0,-,8545702.0,-
Property {axes for special purposes,-,-,-,-,-,-,-,-,-,-
Library,-,-,-,-,-,-,13911751.0,-,13911751.0,-
Parks,-,-,-,-,-,-,8753907.0,-,8753907.0,-
Pargmedic,-,-,-,-,-,-,2335060.0,-,2335060.0,-
Fire,-,-,-,-,-,-,5220824.0,-,5220824.0,-
Sales taxas,-,-,-,-,-,-,12733983.0,-,12733983.0,-
Utilty users taxes,-,-,-,-,-,-,14418851.0,-,14418851.0,-
Trensien occupancy taxes,-,-,-,-,-,-,3673023.0,-,3673023.0,-
Business icense lax,-,-,-,-,-,-,13505958.0,-,13505958.0,-
Other taxes,-,-,-,-,-,-,3440025.0,-,3440025.0,-
Unrestiriclied molor vehicle fees,-,-,-,-,-,-,8543643.0,-,8543643.0,-
Other unrestricted stale subventions,-,-,-,-,-,-,388461.0,-,386481.0,-
Contnbutions not restricted to specific programs,-,-,-,-,-,-,685255.0,-,865255.0,-
Invesiment earmings,-,-,-,-,-,-,5868959.0,1068472.0,6935431.0,-
Miscellaneous,-,-,-,-,-,-,1493684.0,-,1493684.0,386190.0
(Gain on sales of capitel assets,-,-,-,-,-,-,-,10742.0,10742.0,-
Transfers:,-,-,-,-,-,-,-,-,-,-
Primary govemmaent,-,-,-,-,-,-,837018.0,-837018.0,-,-
Total general revenues and transfers,-,-,-,-,-,-,154826242.0,240186.0,155066439.0,386190.0
Changes in net essets,-,-,-,-,-,-,1463244.0,-799053.0,664191328706.0,-4474180.0
Net asseis--beginning (as restated),-,-,-,-,-,-,238238780.0,187277449.0,405516209255128.0,11804640.0
Net assots--ending,-,-,-,-,-,-,230702004.0,166478398.0,406160400581832.0,37130480.0
<snip>
```
