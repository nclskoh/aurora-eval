# Lifted from: https://caendkoelsch.wordpress.com/2019/05/10/merging-multiple-pdfs-into-a-single-pdf/

from PyPDF2 import PdfFileMerger, PdfFileReader
import os

mergedObject = PdfFileMerger()

dir = './testing_logs'
mergedObject.append(PdfFileReader(os.path.join(dir, 'aurora-vs-aurora.pdf'), 'rb'))
mergedObject.append(PdfFileReader(os.path.join(dir, 'vivace-vs-vivace.pdf'), 'rb'))
mergedObject.append(PdfFileReader(os.path.join(dir, 'cubic-vs-cubic.pdf'), 'rb'))
mergedObject.append(PdfFileReader(os.path.join(dir, 'aurora-vs-cubic.pdf'), 'rb'))
mergedObject.append(PdfFileReader(os.path.join(dir, 'cubic-vs-aurora.pdf'), 'rb'))
mergedObject.append(PdfFileReader(os.path.join(dir, 'aurora-vs-vivace.pdf'), 'rb'))
mergedObject.append(PdfFileReader(os.path.join(dir, 'vivace-vs-aurora.pdf'), 'rb'))
mergedObject.append(PdfFileReader(os.path.join(dir, 'vivace-vs-cubic.pdf'), 'rb'))
mergedObject.append(PdfFileReader(os.path.join(dir, 'cubic-vs-vivace.pdf'), 'rb'))

# Write all the files into a file which is named as shown below
mergedObject.write("./fairness_reports.pdf")
