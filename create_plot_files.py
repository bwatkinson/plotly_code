import glob
import re
import argparse
import bisect
import sys
import numpy

acceptable_queries = ['Pass', 'Target', 'Queue', 'Bytes_Xfered', 'Ops'
                      'Elapsed', 'Bandwidth', 'IOPS', 'Latency', 'Pct_CPU',
                      'Xfer_Size']

def get_total_num_passes(basedir):
    num_passes = 0
    # Just grabbing the first file to find total number of passes
    file_names = glob.glob(basedir + '/' + '*.txt')
    with open(file_names[0],'r') as fp:
        xdd_input = fp.readlines()
    # Now finding out the number of passes. The issue is if xdd
    # was not run with verbose, then there is only 1 combined
    # pass output. If not, there are multiple passes to account
    # for.
    for line in xdd_input:
        if 'TARGET_PASS' in line:
            num_passes += 1
    # If there is only 1 combined pass, then we just set to one
    if num_passes == 0:
        num_passes = 1
    return num_passes


def is_passes_xdd_data(basedir):
    # Just grabbing the first file to figure out if it is a pass or run file
    first_file_name = ''
    file_names = glob.glob(basedir + '/' + '*.txt')
    for file_name in file_names:
        first_file_name = file_name
        break
    # Checking to see if file name as passes
    if 'passes' in first_file_name:
        return True
    else:
        # Assumed here that the file name contains runs
        return False


# Getting the threads used for each test
def get_threads(threads, base_dir):
    all_threads = []
    file_names = glob.glob(base_dir + '/' + '*.txt')
    for name in file_names:
        m = re.search('threads_[0-9]+', name)
        if m:
            thread_str = m.group(0)
            m = re.search('[0-9]+', thread_str)
            bisect.insort(all_threads, int(m.group(0)))
    reduced_threads = list(set(all_threads))
    for val in reduced_threads:
        bisect.insort(threads, val)
             

# Getting the total number of runs in input files and threads run
def get_total_num_runs(base_dir):
    all_threads = []
    # Just grab the first file as all files should contain
    # the same number of total runs
    file_names = glob.glob(base_dir + '/' + '*.txt')
    with open(file_names[0]) as fp:
        line = fp.readline()
        run_and_runs = [int(s) for s in line.split() if s.isdigit()]
        # Total Number of Runs
        total_runs = run_and_runs[1]
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
    


def getting_data(base_dir, queries, chart_titles, y_labels, threads, grab):
    offsets = []
    data_points = []
    std_devs = []
    std_errs = []
    run_datapoints = []
    num_passes = 0

    # If we are using XDD pass data, we need to find total number
    # of passes
    if is_passes_xdd_data(base_dir):
        num_passes = get_total_num_passes(base_dir)
    else:
        runs = get_total_num_runs(base_dir)

    # Getting offsets of points of interest
    get_offsets(base_dir, offsets, queries)
    
    # Initializing data points, std_devs, std_errs
    data_points = [[] for l in range(len(queries))]
    std_devs = [[] for l in range(len(queries))]
    std_errs = [[] for l in range(len(queries))]
    
    for t in threads:
        # For each thread we will get the median, standard
        # deviations, and standard error for all queries
        input_file = base_dir + '/'
        path_split = base_dir.split('/')
        input_file += path_split[-1]
        if is_passes_xdd_data(base_dir):
            input_file += '_passes'
        else:
            input_file += '_run_'
        #initializing current runs data sets
        run_datapoints = [[] for l in range(len(queries))]
        if is_passes_xdd_data(base_dir):
            current_input = input_file
            current_input += '_threads_' + str(t) + '.txt'
            input_fp = open(current_input, 'r')
            # Parsing out XDD normal header info
            parse_test_case_header(input_fp, queries)
            # Getting all datapoints
            for p in xrange(num_passes):
                line = input_fp.readline()
                line_list = line.split()
                # Getting data points of interest for this run
                for x in xrange(len(queries)):
                    new_line_list = []
                    # Hacky work around to fix extra tab inserted
                    # in XDD output for certain PASS'es. Our only
                    # hope of fixing this error is if the tab appears
                    # In a floating point number...
                    if len(line_list) > 13:
                        new_line_list = []
                        while len(line_list) != 0:
                            curr_val = line_list.pop(0)
                            float_missing_dec = re.search('^\d+\.\D?$', curr_val)
                            if float_missing_dec:
                                # Found decimal point value missing
                                # values after decimal point, so just
                                # need to combine the values
                                new_line_list.append(curr_val + line_list.pop(0))
                            else:
                                new_line_list.append(curr_val)
                        line_list = new_line_list
                    run_datapoints[x].append(float(line_list[offsets[x]]))
            input_fp.close()
        else:
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
            if grab == 'mean':
                # Getting mean of run values
                data_points[x].append(numpy.mean(run_datapoints[x]))
            if grab == 'median':
                # Getting median of run values
                data_points[x].append(numpy.median(run_datapoints[x]))
            if grab == 'min':
                # Getting min of run values
                data_points[x].append(numpy.min(run_datapoints[x]))
            if grab == 'max':
                # Getting max of run values
                data_points[x].append(numpy.max(run_datapoints[x]))
            # Getting Standard Deviation for Data Points
            std_devs[x].append(numpy.std(run_datapoints[x]))
            # Getting Standard Error for Data Points
            if is_passes_xdd_data(base_dir):
                std_errs[x].append(numpy.std(run_datapoints[x])/(num_passes**0.5))
            else:
                std_errs[x].append(numpy.std(run_datapoints[x])/(runs**0.5))
    
    # Writing out all output to output file
    base_dir_list = base_dir.split('/')
    output_file_name = base_dir_list[len(base_dir_list) - 1]
    output_file_name += '_data.txt'
    write_output_file(output_file_name, queries, threads, data_points, \
                      std_devs, std_errs, chart_titles, y_labels)


def create_bulk_plot_files(plot_dir, xdd_dir, grab):    
    total_runs = 0
    threads = []
    chart_titles = []
    y_labels = []
    queries = []
    xdd_data_dirs = []
    total_runs = -1

    # Grabbing all plot files from plot directory
    plot_file_names = glob.glob(plot_dir + '/' + '*.plot')

    # Generating all xdd data directory paths
    for plot_file_name in plot_file_names:
        base_dir = plot_file_name.split('/')
        base_dir_str = base_dir[len(base_dir) - 1]
        xdd_data_dirs.append(xdd_dir + '/' + base_dir_str.strip('.plot'))

    # Getting the all the threads used, should be same for all.
    # Because of this, just using first directory
    get_threads(threads, xdd_data_dirs[0])
    # Now just generating all plot files
    for plot_file,  xdd_curr_dir in zip(plot_file_names, xdd_data_dirs):
        parse_input_file(plot_file, queries, chart_titles, y_labels)
        getting_data(xdd_curr_dir, 
                     queries, 
                     chart_titles, 
                     y_labels, 
                     threads,
                     grab)
        queries = []
        chart_titles = []
        y_labels = []
                   


                   
def main():
    threads = []
    queries = []
    chart_titles = []
    y_labels = []
    total_runs = -1

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', type=str,
                         help='The base directory to pull input files from, either this and -i are required unless -b is used')
    parser.add_argument('-i', '--input_file', type=str,
                         help='Plot configuration input file, erither this and -d are required unless -b is used')
    parser.add_argument('-b', '--bulk', type=str,
                         help='Do bulk plot operation, either this or -d and -i are required (-b plot_file_dir,xdd_data_dir)')
    parser.add_argument('-g', '--grab', type=str,
                         help='Value to grab can be (mean, median, max, min), median by default')
    
    # Getting Command Line Arguements
    args = parser.parse_args()
    
    # Checking to see if user passed in grab value
    grab = args.grab
    if grab != 'mean' and grab != 'median' and grab != 'max' and grab != 'min':
        grab = 'median'
        print 'Grabbing Median Value'
    else:
        print 'Grabbing ' + grab + ' value'

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
        xdd_dir = bulk_list[1].rstrip('/')
        create_bulk_plot_files(plot_dir, xdd_dir, grab)
    else:
        dir_path = args.directory.rstrip('/')
        get_threads(threads, dir_path)
        parse_input_file(args.input_file, queries, chart_titles, y_labels)
        getting_data(dir_path, 
                     queries, 
                     chart_titles, 
                     y_labels, 
                     threads,
                     grab) 

if __name__ == "__main__":
    main()
