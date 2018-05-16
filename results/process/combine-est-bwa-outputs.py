import csv
import numpy as np
import sys

# Code to be removed if/when estimator is rerun: "mode x" and GC content

def update_table_with_seq(table, rowidx, colidx, seq):
    table[rowidx][colidx]['est'] += 1
    table[rowidx][colidx]['avg_avg_depth'] += seq['avg_depth']
    table[rowidx][colidx]['avg_gc'] += seq['gc']

def fill_row(row, i, table):
    for j in range(1, 6):
        row.extend(table[i][j])

def write_table(tfile, table):
    writer = csv.writer(tfile)
    header = ['Aln/Est']
    for i in range(1, 5):
        header.extend([i, 'Avg avg depth', 'Avg GC content'])
    header.extend(['5+', 'Avg avg depth', 'Avg GC content'])
    writer.writerow(header)
    for i in range(5):
        row = [i]
        fill_row(row, i, table)
        writer.writerow(row)
    row = ['5+']
    fill_row(row, 5, table)
    writer.writerow(row)

def matches(est_count, aln_count):
    if aln_count < 5:
        return (est_count == aln_count)
    else:
        return (est_count >= 5)

def count_ranks(seq, rank_counts, aln_count):
    if aln_count <= 0:
        return
    if matches(seq['1st_label'], aln_count):
        rank_counts[aln_count][0] += 1
    elif matches(seq['2nd_label'], aln_count):
        rank_counts[aln_count][1] += 1
    elif matches(seq['3rd_label'], aln_count):
        rank_counts[aln_count][2] += 1
    else:
        rank_counts[aln_count][3] += 1

def write_ranks(rfile, ranks):
    writer = csv.writer(rfile)
    writer.writerow(['Ref. aln count', 'Likeliest est. #', '2nd likeliest est. #', '3rd likeliest est. #', 'Other'])
    for i in range(1, 6):
        row = [i]
        row.extend(ranks[i])
        writer.writerow(row)

def write_for_r(rfile, header, table, rows, cols):
    writer = csv.writer(rfile)
    writer.writerow(header)
    for i in range(rows):
        for j in range(1, cols):
            row = [i, j]
            row.extend(table[i][j])
            writer.writerow(row)

def write_ranks_for_r(rfile, header, table, rows, cols):
    writer = csv.writer(rfile)
    writer.writerow(header)
    for i in range(1, rows):
        for j in range(cols):
            writer.writerow([i, j+1, table[i][j]])

EST_OUTPUT = sys.argv[1]
BWA_PARSE_OUTPUT = sys.argv[2]
KMER = int(sys.argv[3])
NUMSEQS = int(sys.argv[4])

seqs = np.zeros(NUMSEQS, dtype=[('ID', np.uint64), ('length', np.uint64), ('avg_depth', np.float64), ('gc', np.float64), ('1st_label', np.uint64), ('2nd_label', np.uint64), ('3rd_label', np.uint64), ('aln_match_count', np.uint64), ('aln_other_count', np.uint64), ('aln_other_cigars', np.str), ('aln_mapq', np.int)])
table = np.zeros((6,6), dtype=[('est', np.uint), ('avg_avg_depth', np.float64), ('avg_gc', np.float64)])
table_lt100 = np.zeros((6,6), dtype=[('est', np.uint), ('avg_avg_depth', np.float64), ('avg_gc', np.float64)])
table_lt1000 = np.zeros((6,6), dtype=[('est', np.uint), ('avg_avg_depth', np.float64), ('avg_gc', np.float64)])
table_lt10000 = np.zeros((6,6), dtype=[('est', np.uint), ('avg_avg_depth', np.float64), ('avg_gc', np.float64)])
table_10000plus = np.zeros((6,6), dtype=[('est', np.uint), ('avg_avg_depth', np.float64), ('avg_gc', np.float64)])

rank_counts = np.zeros((6,4), dtype=np.uint)
rank_counts_lt100 = np.zeros((6,4), dtype=np.uint)
rank_counts_lt1000 = np.zeros((6,4), dtype=np.uint)
rank_counts_lt10000 = np.zeros((6,4), dtype=np.uint)
rank_counts_10000plus = np.zeros((6,4), dtype=np.uint)

with open(EST_OUTPUT, newline='') as estfile:
    reader = csv.reader(estfile)
    next(reader)
    for row in reader:
        seqID = int(row[0])
        seqs[seqID]['ID'] = seqID
        seqs[seqID]['length'] = int(row[1])
        seqs[seqID]['avg_depth'] = float(row[2])
        seqs[seqID]['gc'] = float(row[4])
        seqs[seqID]['1st_label'] = int(row[5]) + 1
        seqs[seqID]['2nd_label'] = int(row[6]) + 1
        seqs[seqID]['3rd_label'] = int(row[7]) + 1

with open(BWA_PARSE_OUTPUT, newline='') as alnfile:
    reader = csv.reader(alnfile, delimiter='\t')
    next(reader)
    for row in reader:
        seqID = int(row[0])
        seqs[seqID]['aln_match_count'] = int(row[2])
        seqs[seqID]['aln_other_count'] = int(row[3])
        seqs[seqID]['aln_other_cigars'] = row[4]
        seqs[seqID]['aln_mapq'] = int(row[5])

with open('seq-est-and-aln.csv', 'w', newline='') as seqfile:
    writer = csv.writer(seqfile)
    writer.writerow(['ID', 'Length', 'Average depth', 'GC %', 'Est. 1st label', 'Est. 2nd label', 'Est. 3rd label', 'Ref. alns', 'Ref. other alns', 'Other alns'' CIGARs', 'MAPQ (unique aln only)'])
    for i in range(len(seqs)):
        writer.writerow(list(seqs[i]))

for i in range(len(seqs)):
    rowidx = 5
    colidx = 5
    if seqs[i]['aln_match_count'] < 5:
        rowidx = seqs[i]['aln_match_count']
    if seqs[i]['1st_label'] < 5:
        colidx = seqs[i]['1st_label']
    update_table_with_seq(table, rowidx, colidx, seqs[i])
    count_ranks(seqs[i], rank_counts, rowidx)
    if seqs[i]['length'] < 100:
        update_table_with_seq(table_lt100, rowidx, colidx, seqs[i])
        count_ranks(seqs[i], rank_counts_lt100, rowidx)
    elif seqs[i]['length'] < 1000:
        update_table_with_seq(table_lt1000, rowidx, colidx, seqs[i])
        count_ranks(seqs[i], rank_counts_lt1000, rowidx)
    elif seqs[i]['length'] < 10000:
        update_table_with_seq(table_lt10000, rowidx, colidx, seqs[i])
        count_ranks(seqs[i], rank_counts_lt10000, rowidx)
    else:
        update_table_with_seq(table_10000plus, rowidx, colidx, seqs[i])
        count_ranks(seqs[i], rank_counts_10000plus, rowidx)

for i in range(6):
    for j in range(6):
        if table[i][j]['est'] > 0:
            table[i][j]['avg_avg_depth'] /= table[i][j]['est']
            table[i][j]['avg_gc'] /= table[i][j]['est']
        if table_lt100[i][j]['est'] > 0:
            table_lt100[i][j]['avg_avg_depth'] /= table_lt100[i][j]['est']
            table_lt100[i][j]['avg_gc'] /= table[i][j]['est']
        if table_lt1000[i][j]['est'] > 0:
            table_lt1000[i][j]['avg_avg_depth'] /= table_lt1000[i][j]['est']
            table_lt1000[i][j]['avg_gc'] /= table[i][j]['est']
        if table_lt10000[i][j]['est'] > 0:
            table_lt10000[i][j]['avg_avg_depth'] /= table_lt10000[i][j]['est']
            table_lt10000[i][j]['avg_gc'] /= table[i][j]['est']
        if table_10000plus[i][j]['est'] > 0:
            table_10000plus[i][j]['avg_avg_depth'] /= table_10000plus[i][j]['est']
            table_10000plus[i][j]['avg_gc'] /= table[i][j]['est']

counts_header_for_r = ['aln', 'est', 'count', 'avg_avg_depth', 'avg_gc']
ranks_header_for_r = ['aln', 'est_rank', 'count']

with open('aln-est-counts.csv', 'w') as tfile:
    write_table(tfile, table)
with open('aln-est-counts-r.csv', 'w') as tfile:
    write_for_r(tfile, counts_header_for_r, table, 6, 6)
    
with open('aln-est-counts-lt100.csv', 'w') as tfile:
    write_table(tfile, table_lt100)
with open('aln-est-counts-lt100-r.csv', 'w') as tfile:
    write_for_r(tfile, counts_header_for_r, table_lt100, 6, 6)

with open('aln-est-counts-lt1000.csv', 'w') as tfile:
    write_table(tfile, table_lt1000)
with open('aln-est-counts-lt1000-r.csv', 'w') as tfile:
    write_for_r(tfile, counts_header_for_r, table_lt1000, 6, 6)

with open('aln-est-counts-lt10000.csv', 'w') as tfile:
    write_table(tfile, table_lt10000)
with open('aln-est-counts-lt10000-r.csv', 'w') as tfile:
    write_for_r(tfile, counts_header_for_r, table_lt10000, 6, 6)

with open('aln-est-counts-10000plus.csv', 'w') as tfile:
    write_table(tfile, table_10000plus)
with open('aln-est-counts-10000plus-r.csv', 'w') as tfile:
    write_for_r(tfile, counts_header_for_r, table_10000plus, 6, 6)

with open('aln-est-ranks.csv', 'w') as rfile:
    write_ranks(rfile, rank_counts)
with open('aln-est-ranks-r.csv', 'w') as rfile:
    write_ranks_for_r(rfile, ranks_header_for_r, rank_counts, 6, 4)
    
with open('aln-est-ranks-lt100.csv', 'w') as rfile:
    write_ranks(rfile, rank_counts_lt100)
with open('aln-est-ranks-lt100-r.csv', 'w') as rfile:
    write_ranks_for_r(rfile, ranks_header_for_r, rank_counts_lt100, 6, 4)
    
with open('aln-est-ranks-lt1000.csv', 'w') as rfile:
    write_ranks(rfile, rank_counts_lt1000)
with open('aln-est-ranks-lt1000-r.csv', 'w') as rfile:
    write_ranks_for_r(rfile, ranks_header_for_r, rank_counts_lt1000, 6, 4)
    
with open('aln-est-ranks-lt10000.csv', 'w') as rfile:
    write_ranks(rfile, rank_counts_lt10000)
with open('aln-est-ranks-lt10000-r.csv', 'w') as rfile:
    write_ranks_for_r(rfile, ranks_header_for_r, rank_counts_lt10000, 6, 4)
    
with open('aln-est-ranks-10000plus.csv', 'w') as rfile:
    write_ranks(rfile, rank_counts_10000plus)
with open('aln-est-ranks-10000plus-r.csv', 'w') as rfile:
    write_ranks_for_r(rfile, ranks_header_for_r, rank_counts_10000plus, 6, 4)
    
