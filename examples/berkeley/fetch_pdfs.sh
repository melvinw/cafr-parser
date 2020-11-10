#!/bin/sh
mkdir -p pdf
test -f pdf/2008.pdf || curl -o pdf/2008.pdf "https://www.cityofberkeley.info/uploadedFiles/Finance/Level_3_-_General/FY2008%20CAFR.pdf"
test -f pdf/2009.pdf || curl -o pdf/2009.pdf "https://www.cityofberkeley.info/uploadedFiles/Finance/Level_3_-_General/2009%20CAFR.pdf"
test -f pdf/2010.pdf || curl -o pdf/2010.pdf "https://www.cityofberkeley.info/uploadedFiles/Finance/Level_3_-_General/FY2010%20Berkeley%20CAFR%20Final.pdf"
test -f pdf/2011.pdf || curl -o pdf/2011.pdf "https://www.cityofberkeley.info/uploadedFiles/Finance/Level_3_-_General/BerkeleyCAFRFinal2011.pdf"
test -f pdf/2012.pdf || curl -o pdf/2012.pdf "https://www.cityofberkeley.info/uploadedFiles/Finance/Level_3_-_General/2012%20CAFR.pdf"
test -f pdf/2013.pdf || curl -o pdf/2013.pdf "https://www.cityofberkeley.info/uploadedFiles/Finance/Level_3_-_General/FY2013%20Berkeley%20CAFR%20final%2012-31-2013.pdf"
test -f pdf/2014.pdf || curl -o pdf/2014.pdf "https://www.cityofberkeley.info/uploadedFiles/Finance/Level_3_-_General/FY2014%20Complete%20CAFR.pdf"
test -f pdf/2015.pdf || curl -o pdf/2015.pdf "https://www.cityofberkeley.info/uploadedFiles/Finance/Level_3_-_General/City%20of%20Berkleey%20FY2015%20CAFR%20final%2012-22-2015.pdf"
test -f pdf/2016.pdf || curl -o pdf/2016.pdf "https://www.cityofberkeley.info/uploadedFiles/Finance/Level_3_-_General/FY2016%20Complete%20CAFR.pdf"
test -f pdf/2017.pdf || curl -o pdf/2017.pdf "https://www.cityofberkeley.info/uploadedFiles/Finance/Level_3_-_General/2017%20CAFR%20-%20City%20of%20Berkeley.pdf"
test -f pdf/2018.pdf || curl -o pdf/2018.pdf "https://www.cityofberkeley.info/uploadedFiles/Finance/Home/Reports/BerkeleyCAFRReport2018.pdf"
test -f pdf/2019.pdf || curl -o pdf/2019.pdf "https://www.cityofberkeley.info/uploadedFiles/Finance/Level_3_-_General/FY2019CAFRReport.pdf"
