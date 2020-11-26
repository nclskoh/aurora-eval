# Lifted from: https://caendkoelsch.wordpress.com/2019/05/10/merging-multiple-pdfs-into-a-single-pdf/

from PyPDF2 import PdfFileMerger, PdfFileReader
import argparse
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Merge fairness results for all-pairs experiment")
    parser.add_argument('--dir', '-d', help='directory containing fairness log files', required=True)
    parser.add_argument('--out', '-o', help='file to write to', required=True)

    args = parser.parse_args()

    mergedObject = PdfFileMerger()

    dir = args.dir
    mergedObject.append(PdfFileReader(os.path.join(dir, 'aurora-vs-aurora.pdf'), 'rb'))
    mergedObject.append(PdfFileReader(os.path.join(dir, 'vivace-vs-vivace.pdf'), 'rb'))
    mergedObject.append(PdfFileReader(os.path.join(dir, 'cubic-vs-cubic.pdf'), 'rb'))
    mergedObject.append(PdfFileReader(os.path.join(dir, 'aurora-vs-cubic.pdf'), 'rb'))
    mergedObject.append(PdfFileReader(os.path.join(dir, 'cubic-vs-aurora.pdf'), 'rb'))
    mergedObject.append(PdfFileReader(os.path.join(dir, 'aurora-vs-vivace.pdf'), 'rb'))
    mergedObject.append(PdfFileReader(os.path.join(dir, 'vivace-vs-aurora.pdf'), 'rb'))
    mergedObject.append(PdfFileReader(os.path.join(dir, 'vivace-vs-cubic.pdf'), 'rb'))
    mergedObject.append(PdfFileReader(os.path.join(dir, 'cubic-vs-vivace.pdf'), 'rb'))

    mergedObject.write(args.out)
