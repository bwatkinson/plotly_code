import argparse
import sys
import numpy

def is_float(x):
    try:
        float(x)
        return True
    except:
        return False



def write_gnu_output_data(x_vals, y_vals, data_file_num):
    try:
        fp = open('gnu_plot_data' + str(data_file_num) + '.dat', 'w')
    except:
        print 'Could not open, gnu_plot_data' + str(data_file_num) + '.dat...'
        exit(1)

    for x in xrange(len(x_vals[0])):
        fp.write(str(x_vals[0][x]) + '\t')
        for y in xrange(len(y_vals)):
            if y_vals[y][x] == y_vals[len(y_vals) - 1][x]:
                fp.write(str(y_vals[y][x]))
            else:
                fp.write(str(y_vals[y][x]) + '\t')
        fp.write('\n')



def write_gnu_output(chart_title, chart_type, x_label, y_label, legend_val, x_vals, 
                     y_vals, std_dev, std_err, x_max, y_max, y_min, data_file_num, baseline,
                     all_labels, labels):
    try:
        fp = open('gnu_plot' + str(data_file_num) + '.plt', 'w')
    except:
        print 'Could not open, gnu_plot' + str(data_file_num) + '.plt...'
        exit(1)
    
    base_line_vals = []
    median_x = numpy.median(x_vals[0])
    
    fp.write('#!/usr/bin/env gnuplot\n\n')
    fp.write('# Terminal\n')
    fp.write('set terminal pngcairo enhanced size 640,480 font \"Helvetica,16\"\n\n')
    fp.write('## Setup a pretty grid\n')
    fp.write('set style line 11 lc rgb \"#404040\" lt 1\n')
    fp.write('set border 3 back ls 11\n')
    fp.write('set tics nomirror\n')
    fp.write('set style line 12 lc rgb \"#404040\" lt 0 lw 0.5\n')
    fp.write('set grid back ls 12\n\n')
    fp.write('## Line styles\n')
    fp.write('# Baseline Line style\n')
    fp.write('set style line 1 lt 3 dt 2 lw 3 lc rgb \"#000000\"\n')
    fp.write('# All Other Line Styles\n')
    fp.write('set style line 2 lt 2 lw 3 pt 1 lc rgb \"#ece2f0\"\n')
    fp.write('set style line 3 lt 2 lw 3 pt 2 lc rgb \"#d0d1e6\"\n')
    fp.write('set style line 4 lt 2 lw 3 pt 3 lc rgb \"#a6bddb\"\n')
    fp.write('set style line 5 lt 2 lw 3 pt 4 lc rgb \"#67a9cf\"\n')
    fp.write('set style line 6 lt 2 lw 3 pt 5 lc rgb \"#3690c0\"\n')
    fp.write('set style line 7 lt 2 lw 3 pt 7 lc rgb \"#02818a\"\n')
    fp.write('set style line 8 lt 2 lw 3 pt 11 lc rgb \"#016c59\"\n')
    fp.write('set style line 9 lt 2 lw 3 pt 13 lc rgb \"#014636\"\n\n')
    #fp.write('## Setting label to annotate ZFS Settings\n')
    #fp.write('set label 1 at ' + str(median_x) + ',' + str(y_max) + '\n')
    #fp.write('set label 1 \"Put text here\"\n\n')
    fp.write('## Setting up plot data\n')
    fp.write('set output \"plot.png\"\n')
    fp.write('unset log\n')
    fp.write('unset label\n')
    fp.write('set ytic auto\n')
    fp.write('set grid\n')
    fp.write('set key outside font \"Helvetica,10\"\n')
    fp.write('set title \"' + chart_title[0] + '\"\n')
    fp.write('set xlabel \"' + x_label[0] + '"\n')
    fp.write('set ylabel \"' + y_label[0] + '"\n')
    fp.write('set yrange[0:' + str(y_max + 100) + ']\n')
    fp.write('set xrange[-1:' + str(int(x_max) + 1) + ']\n')
    # Setting up line style for baseline
    if baseline != None:
        base_line_vals = baseline.split(',')
        if len(base_line_vals) == 2:
            base_line_name = base_line_vals[0] + ' (' + base_line_vals[1] + ')'
            base_line_y = base_line_vals[1]
            # If the user defined a baseline, we need to create the function
            fp.write('# basline function\n')
            fp.write('f(x) = ' + str(base_line_y) + '\n')
        else:
            print 'Base line requires Name and Value... Not adding baseline'

    if chart_type[0] == 'line':  
        # If it is a line graph, we write this to the header
        fp.write('set xtics(')
        for x in x_vals[0]:
            if x == x_vals[0][len(x_vals[0]) - 1]:
                fp.write(str(x))
            else:
                fp.write(str(x) + ',')
        fp.write(')\n')
    elif chart_type[0] == 'bar':
        # If this is a bar graph, we write this to the header
        fp.write('set style histogram clustered gap 1')
        fp.write('set style data histogram')
        fp.write('set style fill solid')
        fp.write('set boxwidth 1.0')

    # Now just going to write out plot line    
    for x in xrange(len(x_vals)):
        if chart_type[0] == 'line':
            if x == 0:
                # Only on the first line do we need to put plot command
                fp.write('plot \"gnu_plot_data' + str(data_file_num) + '.dat\" using 1:'
                         + str(x + 2) + ' title \"' + legend_val[x] + '\" with lp,\\\n')
            else:
                fp.write('\t\"\" using 1:' + str(x + 2) + ' title \"' + legend_val[x] + 
                        '\" with lp,\\\n')
        elif chart_type[0] == 'bar':
            if x == 0:
                # Only on the first line do we need to put plot command and xticlabels
                fp.write('plot \"gnu_plot_data' + str(data_file_num) + '.dat\" using '
                         + str(x + 2) + ':xticlabels(1) title \"' + legend_val[x] + '\\\n"') 
            else:
                fp.write('\t\"\" using ' + str(x + 2) + ' title \"' + legend_label[x] + 
                "\"\\\n")
  
    # Now adding labels if requested
    if all_labels:
        if chart_type[0] == 'line':
            for y in xrange(len(y_vals)):
                fp.write('\t\"\" using 1:' + str(y + 2) + ':(sprintf(\"%.3f\",column(' + str(y + 2) + 
                         '))) notitle with labels offset 0,0.5 font \"Helvtica,8\",\\\n')
        elif chart_type[0] == 'bar':
            for y in xrange(len(y_vals)):
                fp.write('\t\"\" using 0:' + str(y + 2) + ':(sprintf(\"0.3f\",column(' + str(y + 2) +
                         '))) notitle with labels offset 0,0.8 font \"Helvetica,8\",\\\n')

    elif labels != None:
        labels_split = labels.split(',')
        if chart_type[0] == 'line':
            for label in labels_split:
                label_val = int(label)
                if label_val <= len(y_vals):
                    fp.write('\t\"\" using 1:' + str(label_val + 1) + ':(sprintf(\"%.3f\",column(' + str(label_val + 1) +
                             '))) notitle with labels offset 0,0.5 font \"Helvetica,8\",\\\n')
        elif chart_type[0] == 'bar':
            for label in label_split:
                label_val = int(label)
                if label_val <= len(y_vals):
                    fp.write('\t\"\" using 0:' + str(label_val + 1) + ':sprintf(\"%.3f\",column(' + str(label_val + 1) +
                             '))) notitle with labels offset 0,0.5 font \"Helvetica,8\",\\\n')


    # If baseline requested, we will now place it
    if baseline != None:
        fp.write('\tf(x) ls 1 title \"' + base_line_name + '\"')

    fp.close()


def determine_max_min_vals(x_vals, y_vals):
    x_max = 0
    y_max = 0
    y_min = float('inf') 
   
    # First determining x maximum 
    for x in x_vals:
        curr_max = max(x)
        if curr_max > x_max:
            x_max = curr_max
    # Next determining y max and minimum
    for y in y_vals:
        curr_max = max(y)
        curr_min = min(y)
        if curr_max > y_max:
            y_max = curr_max
        if curr_min < y_min:
            y_min = curr_min

    return [x_max, y_max, y_min]


def create_output_files(input_file, baseline, y_range_max,
                        all_labels, labels):

    total_dataset = 0
    poi_per_dataset = 0
    one_plot = False

    fp = open(input_file, 'r')
    # Finding out how many datasets are in the plot file and
    # how many point of interests there are per dataset. Also,
    # determining if all datasets are going to be on one plot
    # or multiple plots
    line = fp.readline()
    line_split = line.split()
    if line_split[len(line_split) - 1] == 'ALL':
        one_plot = True
    total_datasets = int(line_split[0])
    poi_per_dataset = int(line_split[1])

    # Setting up lists and values
    chart_titles = []
    chart_types = []
    x_labels = []
    y_labels = []
    legend_vals = []
    x_vals = []
    y_vals = []
    std_devs = []
    std_errs = []
    x_max = 0
    y_max = 0
    y_min = 0

    line = fp.readline()
    # Now just reading till the end of the file
    while line:
        curr_x_vals = []
        line_split = line.split(',')
        if 'x-title' in line_split[0]:
            x_labels.append(line_split[1])
            line = fp.readline()
            line_split = line.split(',')[0].split()
            if 'Threads' in line_split or 'Targets' in line_split:
                # We are dealing with a bar graph, so we just need
                # to update the values to be ints
                line_split = line.split(',')
                for x in line_split:
                    x_vals_split = x.split()
                    for y in x_vals_split:
                        if y.isdigit():
                            curr_x_vals.append(y)
                line_split = curr_x_vals
            x_vals.append([int(s) for s in line_split if s.isdigit()])
            line = fp.readline()
        elif 'y-title' in line_split[0]:
            y_labels.append(line_split[1])
            legend_vals.append(line_split[2].rstrip())
            line = fp.readline()
            line_split = line.split(',')[0].split()
            y_vals.append([float(s) for s in line_split if is_float(s)])
            line = fp.readline()
        elif 'line' in line_split[0] or 'bar' in line_split[0]:
            chart_types.append(line_split[0].replace('# ',''))
            chart_titles.append(line_split[1].replace('<br>','\\n'))
            line = fp.readline()
        elif 'STDDEV' in line_split[0]:
            line = fp.readline()
            line_split = line.split(',')[0].split()
            std_devs.append([float(s) for s in line_split if is_float(s)])
            line = fp.readline() 
        elif 'STDERR' in line_split[0]:
            line = fp.readline()
            line_split = line.split(',')[0].split()
            std_errs.append([float(s) for s in line_split if is_float(s)])
            line = fp.readline()
        else:
            # Unrecognized label just skipping
            line = fp.readline()
    
    if not one_plot:
        # Will generate gnu files for every value
        for x in xrange(len(x_vals)):
            # max_min_vals = [x_max, y_max, y_min]
            max_min_vals = determine_max_min_vals([x_vals[x]], [y_vals[x]])
            if y_range_max != None:
                # Manually setting y_max from command line
                max_min_vals[1] = y_range_max
            write_gnu_output_data([x_vals[x]], [y_vals[x]], x)
            write_gnu_output([chart_titles[x]], [chart_types[x]], 
                             [x_labels[x]], [y_labels[x]], [legend_vals[x]], 
                             [x_vals[x]], [y_vals[x]], [std_devs[x]], 
                             [std_errs[x]], max_min_vals[0], max_min_vals[1], 
                             max_min_vals[2], x, baseline, all_labels, labels)
    else:
        # Just need to generate a single gnu data and plot file for all data sets     
        
        # max_min_vals = [x_max, y_max, y_min]
        max_min_vals = determine_max_min_vals(x_vals, y_vals)
        if y_range_max != None:
            # Manually setting y_max from command line
            max_min_vals[1] = y_range_max
        write_gnu_output_data(x_vals, y_vals, 0)
        write_gnu_output(chart_titles, chart_types, x_labels, y_labels, legend_vals, x_vals, 
                         y_vals, std_devs, std_errs, max_min_vals[0], max_min_vals[1], 
                         max_min_vals[2], 0, baseline, all_labels, labels)




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_file', type=str,
                        help='Plot configuration file',
                        required=True)
    parser.add_argument('-b', '--baseline', type=str,
                        help='String and value to create baseline on plot EX: \"Device Max,5031.931\"')
    parser.add_argument('-y', '--y_range_max', type=float,
                        help='Sets the maxium value on the y-axis of the gnuplot output')
    parser.add_argument('-a', '--all_labels', dest='all_lables', action='store_true',
                        help='If passed, will add labels to data points in the gnuplot output')
    parser.add_argument('-l', '--labels', type=str,
                        help='Adds labels only to the traces listed as the values from 1 to n seperated by commas')
    parser.set_defaults(all_labels=False)

    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        exit(1)

    try:
        fp = open(args.input_file)
        fp.close()
    except:
        print 'Invalid file passed into script...'
        exit(1)

    create_output_files(args.input_file,
                        args.baseline,
                        args.y_range_max,
                        args.all_labels,
                        args.labels)

if __name__ == '__main__':
    main()
