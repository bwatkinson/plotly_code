import glob
import re
import argparse
import bisect
import sys
import numpy

acceptable_queries = ['Pass', 'Target', 'Queue', 'Bytes_Xfered', 'Ops'
                      'Elapsed', 'Bandwidth', 'IOPS', 'Latency', 'Pct_CPU',
                      'Xfer_Size']


# Getting the total number of runs in input files and threads run
def get_total_num_runs_and_threads(base_dir, threads):
    all_threads = []
    # Just grab the first file as all files should contain
    # the same number of total runs
    file_names = glob.glob(base_dir + '/' + '*.txt')
    with open(file_names[0]) as fp:
        line = fp.readline()
        run_and_runs = [int(s) for s in line.split() if s.isdigit()]
        # Total Number of Runs
        total_runs = run_and_runs[1]
    for name in file_names:
        m = re.search('threads_[0-9]+', name)
        if m:
            thread_str = m.group(0)
            m = re.search('[0-9]+', thread_str)
            bisect.insort(all_threads, int(m.group(0)))
    reduced_threads = list(set(all_threads))
    for val in reduced_threads:
        bisect.insort(threads, val)
    return total_runs



def parse_input_file(input_file, queries, chart_titles, y_labels):
    with open(input_file, 'r') as fp:
        line = fp.readline()
        # Getting rid of comments at top of file
        while '#' in line:
            line = fp.readline()
        line_split = line.split()
        for i in line_split:
            queries.append(i)
        for x in xrange(len(queries)):
            line = fp.readline()
            # Getting rid of possible comments
            while '#' in line:
                line = fp.readline()
            chart_titles.append(line)
            line = fp.readline()
            # Getting rid of possible comments
            while '#' in line:
                line = fp.readline()
            y_labels.append(line)

    # Making sure Queries are valid
    for val in queries:
        if val not in acceptable_queries:
            print val + ' is not a valid query'
            print 'Exiting program...' 
            exit(1)

def parse_test_case_header(fp, queries):
    #looking for DD command output, so will skip everything else
    line = fp.readline()
    while line.find(queries[0]) == -1:
        line = fp.readline()
    fp.readline()



def write_output_file(output_file_name, queries, threads, data_points, \
                      std_devs, std_errs, chart_titles, y_labels):
    fp = open(output_file_name, 'w')
    # Writing out how many data sets there are along with each
    # datasets corresponding values
    fp.write(str(len(data_points)) + ' ' + '3\n')
    # Writing out the x values
    fp.write('# x-title,Number of I/O Threads\n')
    for x in threads:
        fp.write(str(x) + ' ')
    fp.write('\n')
    for x in xrange(len(data_points)):
        y_label_split = y_labels[x].split(',')
        # Writing out chart titles
        fp.write('# ')
        fp.write(chart_titles[x].rstrip() + ',' + queries[x] + '\n')
        # Writing out the y labels
        fp.write('# y-title,')
        fp.write(y_labels[x].rstrip() + ',' + queries[x] + '\n')
        # Writing out y data values
        for y in xrange(len(data_points[x])):
            fp.write(str('%.3f' % data_points[x][y]) + ' ')
        fp.write('\n')
        # Writing out standard deviations
        fp.write('# STDDEV,' + queries[x] + '\n')
        for y in xrange(len(std_devs[x])):
            fp.write(str('%.3f' % std_devs[x][y]) + ' ')
        fp.write('\n')
        # Writing out standard errors
        fp.write('# STDERR,' + queries[x] + '\n')
        for y in xrange(len(std_errs[x])):
            fp.write(str('%.3f' % std_errs[x][y]) + ' ')
        fp.write('\n')
    fp.close()    



def get_offsets(base_dir, offsets, queries):
    file_names = glob.glob(base_dir + '/' + '*.txt')
    # Just grabbing the first file as it doesn't really matter
    # what the file is, because of the offsets will be the same 
    with open(file_names[0]) as fp:
        line = fp.readline()
        while line.find(queries[0]) == -1:
            line = fp.readline()
        line_list = line.split()
        for x in queries:
            offsets.append(line_list.index(x))
    


def getting_data(base_dir, queries, chart_titles, y_labels, threads, runs):
    offsets = []
    data_points = []
    std_devs = []
    std_errs = []
    run_datapoints = []

    # Getting offsets of points of interest
    get_offsets(base_dir, offsets, queries)
    
    # Initializing data points, std_devs, std_errs
    data_points = [[] for l in range(len(queries))]
    std_devs = [[] for l in range(len(queries))]
    std_errs = [[] for l in range(len(queries))]

    for t in threads:
        # For each thread we will get the mean, standard
        # deviations, and standard error for IOPS and 
        # throughputs over the number of runs
        input_file = base_dir + '/'
        path_split = base_dir.split('/')
        input_file += path_split[-1]
        input_file += '_run_'
        #initializing current runs data sets
        run_datapoints = [[] for l in range(len(queries))]
        for r in range(1,runs+1):
             # Getting current input based on run #
             current_input = input_file
             current_input += str(r) + '_threads_' + str(t) + '.txt'
             input_fp = open(current_input, 'r')
             # Parsing out XDD normal header info
             parse_test_case_header(input_fp, queries)
             line = input_fp.readline()
             line_list = line.split()
             # Getting data points of interest for this run
             for x in xrange(len(queries)):
                 run_datapoints[x].append(float(line_list[offsets[x]]))
             input_fp.close()
        
        for x in xrange(len(queries)):  
            # Getting mean values of data
            data_points[x].append(numpy.median(run_datapoints[x]))
            # Getting Standard Deviation for Data Points
            std_devs[x].append(numpy.std(run_datapoints[x]))
            # Getting Standard Error for Data Points
            std_errs[x].append(numpy.std(run_datapoints[x])/(runs**0.5))
    
    # Writing out all output to output file
    base_dir_list = base_dir.split('/')
    output_file_name = base_dir_list[len(base_dir_list) - 1]
    output_file_name += '_data.txt'
    write_output_file(output_file_name, queries, threads, data_points, \
                      std_devs, std_errs, chart_titles, y_labels)


def create_bulk_plot_files(plot_dir, xdd_dir):    
    total_runs = 0
    threads = []
    chart_titles = []
    y_labelss = []
    queries = []
    xdd_data_dirs = []

    # Grabbing all plot files from plot directory
    plot_file_names = glob.glob(plot_dir + '/' + '*.plot')

    # Generating all xdd data directory paths
    for plot_file_name in plot_file_names:
        xdd_data_dirs.append(xdd_dir + '/' + plot_file_name.strip('.plot'))

    # Just using the first file to get total runs
    total_runs = get_total_num_runs_and_threads(xdd_data_dirs[0], threads)
    
    # Now just generating all plot files
    for plot_file,  xdd_curr_dir in zip(plot_file_names, xdd_data_dirs):
        parse_input_file(plot_file, queries, chart_titles, y_labels)
        getting_data(xdd_curr_dir, 
                     queries, 
                     chart_titles, 
                     y_labels, 
                     threads, 
                     total_runs)
        queries = []
        chart_titles = []
        y_labels = []
                   
                    
def main():
    threads = []
    queries = []
    chart_titles = []
    y_labels = []

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', type=str,
                         help='The base directory to pull input files from, either this and -i are required unless -b is used')
    parser.add_argument('-i', '--input_file', type=str,
                         help='Plot configuration input file, erither this and -d are required unless -b is used')
    parser.add_argument('-b', '--bulk', type=str,
                         help='Do bulk plot operation, either this or -d and -i are required (-b plot_file_dir,xdd_data_dir)')
    
    # Getting Command Line Arguements
    args = parser.parse_args()
    
    # Checking to make sure requirements are meet
    if args.directory is None and args.input_file is None and args.bulk is None:
        # Error Either -d and -i must be set or -b must be set
        parser.print_help()
        sys.exit(0)    
    elif args.bulk is None:
        if args.directory is None or args.input_file is None:
            # If not using bulk then then -d and -i must bet set
            parser.print_help()
            sys.exit(0)
    
    if args.bulk is not None:
        bulk_list = args.bulk.split(',')
        plot_dir = bulk_list[0].rstrip('/')
        xdd_dir = bulk_list[1].rstip('/')
        create_bulk_plot_files(plot_dir, xdd_dir)
    else:
        dir_path = args.directory.rstrip('/')

        total_runs = get_total_num_runs_and_threads(dir_path, threads)
    
        parse_input_file(args.input_file, queries, chart_titles, y_labels)

        getting_data(dir_path, 
                     queries, 
                     chart_titles, 
                     y_labels, 
                     threads, 
                     total_runs)

if __name__ == "__main__":
    main()
