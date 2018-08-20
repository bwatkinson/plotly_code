import glob
import re
import argparse
import bisect
import sys
import numpy

acceptable_queries = ['Pass', 'Target', 'Queue', 'Bytes_Xfered', 'Ops'
                      'Elapsed', 'Bandwidth', 'IOPS', 'Latency', 'Pct_CPU',
                      'Xfer_Size', 'Compress_Size', 'Physical_Bandwidth',
                      'Combined_Bandwidth', 'Combined_CPU', 
                      'Combined_Physical_Bandwidth']

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
    # Checking to see if file name has passes
    if 'passes' in first_file_name:
        return True
    else:
        # Assumed here that the file name contains runs
        return False


def is_num_files(basedir):
    # Just grabbing the first file to figure out if it is a num_files output
    first_file_name = ''
    file_names = glob.glob(basedir + '/' + '*.txt')
    for file_name in file_names:
        first_file_name = file_name
        break
    # Checking to see if the file name has num_files
    if 'num_files' in first_file_name:
        return True
    else:
        # Assumed here the file name either contains runs or passes
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
             

# Getting the number of files used per thread
def get_num_files(num_files, base_dir):
    file_names = glob.glob(base_dir + '/' + '*.txt')
    for name in file_names:
        m = re.search('num_files_[0-9]+', name)
        if m:
            num_file_str = m.group(0)
            m = re.search('[0-9]+', num_file_str)
            if m and int(m.group(0)) not in num_files:
                bisect.insort(num_files, int(m.group(0)))


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

    # Updating query list if Physical_Bandwidth is a query
    physical_index = -1
    try:
        physical_index = queries.index('Physical_Bandwidth')
        queries.pop(physical_index)
        queries.append('Physical_Bandwidth')
        # Moving the chart titles and y labels
        phys_chart_title = chart_titles.pop(physical_index)
        chart_titles.append(phys_chart_title)
        phys_y_label = y_labels.pop(physical_index)
        y_labels.append(phys_y_label)
    except:
        # Nothing to do, so don't worry about it
        pass


    # Now need to place Compression Size at the end of the list
    # if it is a query
    compress_size_index = -1
    try:
        compress_size_index = queries.index('Compress_Size')
        queries.pop(compress_size_index)
        queries.append('Compress_Size')
        # Moving the chart titles and y labels
        comp_size_chart_title = chart_titles.pop(compress_size_index)
        chart_titles.append(comp_size_chart_title)
        comp_y_label = y_labels.pop(compress_size_index)
        y_labels.append(comp_y_label)
    except:
        # Nothing to do, so don't worry about it
        pass


def parse_test_case_header(fp, queries):
    # Need to make sure that Combined searches are not the only thing
    # we are searching for. If so we do not need to parse here.
    ignore_list = ['Combined_Bandwidth','Combined_CPU','Combined_Physical_Bandwidth']
    if set(ignore_list) == set(queries):
        return
    elif len(queries) == 1 and 'Combined' in queries[0]:
        return

    query_offset = 0
    while 'Combined' in queries[query_offset] and query_offset < len(queries) - 1:
        query_offset += 1
    
    if query_offset == 1:
        # All queries are for Combined data values, so just dont need
        # to parse the header
        return

    #looking for DD command output, so will skip everything else
    line = fp.readline()
    while line.find(queries[query_offset]) == -1:
        line = fp.readline()
    fp.readline()


def jump_to_zfs_list_input(fp):
    #looking for MOUNTPOINT
    last_pos = fp.tell()
    line = fp.readline()
    while line.find('MOUNTPOINT') == -1:
        line = fp.readline()
    return last_pos


def jump_to_xdd_combined_input(input_fp):
    #looking for 
    last_pos = input_fp.tell()
    line = input_fp.readline()
    while line.find('COMBINED') == -1:
        line = input_fp.readline()
        line_list = line.split()
    return [last_pos, line_list]


def correct_xdd_output(line_list, xdd_file_offset):
    # Hacky work around to fix extra tab inserted
    # in XDD output for certain PASS'es. Our only
    # hope of fixing this error is if the tab appears
    # In a floating point number...
    # or TARGET_PASS/TARGET_AVERAGE being split...
    # or occurs in Bandwidth on line 8...
    new_line_list = []
    if xdd_file_offset == 8:
        curr_offset = 0
        while len(line_list) != 0:
            curr_val = line_list.pop(0)
            if curr_offset == 7:
                new_line_list.append(curr_val + line_list.pop(0))
            else:
                new_line_list.append(curr_val)
            curr_offset += 1
    elif 'COMBINED' in line_list:
        curr_offset = 0
        while len(line_list) != 0:
            curr_val = line_list.pop(0)
            if curr_offset == 7:
                new_line_list.append(curr_val + line_list.pop(0))
            else:
                new_line_list.append(curr_val)
            curr_offset += 1
    else:
        while len(line_list) != 0:
            curr_val = line_list.pop(0)
            float_missing_dec = re.search('^\d+\.\D?$', curr_val)
            if curr_val == 'TARGET_P' or curr_val == 'TARGET_A':
                new_line_list.append(curr_val + line_list.pop(0))
            elif float_missing_dec:
                # Found decimal point value missing
                # values after decimal point, so just
                # need to combine the values
                new_line_list.append(curr_val + line_list.pop(0))
            else:
                new_line_list.append(curr_val)
    return new_line_list


def write_output_file(output_file_name, queries, threads, data_points, \
                      std_devs, std_errs, chart_titles, y_labels):
    fp = open(output_file_name, 'w')
    # Writing out how many data sets there are along with each
    # datasets corresponding values
    fp.write(str(len(data_points)) + ' ' + '3\n')
    for x in xrange(len(data_points)):
        # Writing out the x values
        fp.write('# x-title,Number of I/O Threads,' + queries[x] + '\n')
        for t in threads:
            if chart_titles[x].split(',')[0] == 'line':
                fp.write(str(t) + ' ')
            elif chart_titles[x].split(',')[0] == 'bar':
                fp.write(str(t) + ' Threads, ')
        fp.write(queries[x] + '\n')
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



def write_output_file_num_files_for_threads(output_file_name, queries, threads, data_points, \
                                            std_devs, std_errs, chart_titles, y_labels, num_files):
    fp = open(output_file_name, 'w')
    # Writing out how many data sets there are along with each
    # datasets corresponding values
    fp.write(str(len(data_points[0]) * len(queries)) + ' ' + '3\n')
    for x in xrange(len(queries)):
        for y in xrange(len(data_points[0])):
            tag = queries[x] + ' for ' + str(num_files[y]) + ' files'
            # Writing out the x values
            fp.write('# x-title,Number of I/O Threads Per File,' + tag + '\n')
            for t in threads:
                if chart_titles[x].split(',')[0] == 'line':
                    if t == threads[len(threads) - 1]:
                        fp.write(str(t) + ',')
                    else:
                        fp.write(str(t) + ' ')
                elif chart_titles[x].split(',')[0] == 'bar':
                    fp.write(str(t) + ' Threads, ')
            fp.write(tag + '\n')
            y_label_split = y_labels[x].split(',')
            # Writing out chart titles
            fp.write('# ')
            fp.write(chart_titles[x].rstrip() + ',' + tag + '\n')
            # Writing out the y labels
            fp.write('# y-title,')
            fp.write(y_labels[x].rstrip() + ',' + tag + '\n')
            # Writing out y data values
            for z in xrange(len(data_points[x][y])):
                fp.write(str('%.3f' % data_points[x][y][z]) + ' ')
            fp.write('\n')
            # Writing out standard deviations
            fp.write('# STDDEV,' + tag + '\n')
            for z in xrange(len(std_devs[x][y])):
                fp.write(str('%.3f' % std_devs[x][y][z]) + ' ')
            fp.write('\n')
            # Writing out standard errors
            fp.write('# STDERR,' + tag + '\n')
            for z in xrange(len(std_errs[x][y])):
                fp.write(str('%.3f' % std_errs[x][y][z]) + ' ')
            fp.write('\n')
    fp.close()    



def write_output_file_num_files_for_files(output_file_name, queries, threads, data_points, \
                                          std_devs, std_errs, chart_titles, y_labels, num_files):
    
    fp = open(output_file_name, 'w')
    # Writing out how many data sets there are along with each
    # datasets corresponding values
    fp.write(str(len(threads) * len(queries)) + ' ' + '3\n')
    for x in xrange(len(queries)):
        for y in xrange(len(data_points[0][0])):
            tag = queries[x] + ' for ' + str(threads[y]) + ' threads'
            # Writing out the x values
            fp.write('# x-title,Number of Target Files,' + tag + '\n')
            for n in num_files:
                if chart_titles[x].split(',')[0] == 'line':
                    if n == num_files[len(num_files) - 1]:
                        fp.write(str(n) + ',')
                    else:
                        fp.write(str(n) + ' ')
                elif chart_titles[x].split(',')[0] == 'bar':
                    fp.write(str(n) + ' Targets, ')
            fp.write(tag + '\n')
            y_label_split = y_labels[x].split(',')
            # Writing out chart titles
            fp.write('# ')
            fp.write(chart_titles[x].rstrip() + ',' + tag + '\n')
            # Writing out the y labels
            fp.write('# y-title,')
            fp.write(y_labels[x].rstrip() + ',' + tag + '\n')
            # Writing out y data values
            for z in xrange(len(data_points[x])):
                fp.write(str('%.3f' % data_points[x][z][y]) + ' ')
            fp.write('\n')
            # Writing out standard deviations
            fp.write('# STDDEV,' + tag + '\n')
            for z in xrange(len(std_devs[x])):
                fp.write(str('%.3f' % std_devs[x][z][y]) + ' ')
            fp.write('\n')
            # Writing out standard errors
            fp.write('# STDERR,' + tag + '\n')
            for z in xrange(len(std_errs[x])):
                fp.write(str('%.3f' % std_errs[x][z][y]) + ' ')
            fp.write('\n')
    fp.close()    



def get_offsets(base_dir, offsets, queries):
    zfs_list_ouput_present = False
    set_compress_size_offset = False

    # Just grabbing the first file as it doesn't really matter
    # what the file is, because of the offsets will be the same 
    file_names = glob.glob(base_dir + '/' + '*.txt')
   
    # If either the query Physical_Bandwidth or Compress_Size
    # is desired, we first must make sure that the output file
    # has the proper ZFS list output. If it doesn't we will
    # just bail
    if 'Physical_Bandwidth' in queries or 'Compress_Size' in queries or 'Combined_Physical_Bandwidth':
        with open(file_names[0]) as fp:
            line = fp.readline()
            while line:
                if line.find('MOUNTPOINT') != -1:
                    zfs_list_output_present = True
                    break
                line = fp.readline()
        if zfs_list_output_present != True:
            print 'In order to query Physical_Bandwidth or Compress_size the output must'
            print 'contain the output from zfs list... Exiting'
            exit(1)

    copy_queries = list(queries)
    
    # If the query is Physical_Bandwidth, need to update the
    # query value to search for to Elapsed. We are merely
    # getting the total time to transfer data
    physical_index = -1
    try:
        physical_index = copy_queries.index('Physical_Bandwidth')
        copy_queries[physical_index] = 'Elapsed'
    except:
        # Nothing to do, so don't worry about it
        pass

    # If Compress_Size is a query we know of the offset, so we will
    # just manually set it
    compress_size_index = -1
    try:
        compress_size_index = copy_queries.index('Compress_Size')
        set_compress_size_offset = True
    except:
        # Nothing to do, so don't worry about it
        pass

    # if the query is Combined_Bandwidth, need to update the
    # query value to search for Bandwidth
    combined_bandwidth_index = -1
    try:
        combined_bandwidth_index = copy_queries.index('Combined_Bandwidth')
        copy_queries[combined_bandwidth_index] = 'Bandwidth'
    except:
        # Nothing to do, so don't worry about it
        pass

    # if query is Combined_CPU, need to update the query value
    # to search for Pct_CPU
    combined_cpu_index = -1
    try:
        combined_cpu_index = copy_queries.index('Combined_CPU')
        copy_queries[combined_cpu_index] = 'Pct_CPU'
    except:
        # Nothing to do, so dont worry about it
        pass

    # if the query is Combined_Physical_Bandwidth, need to update
    # the query value to search for Elapsed. We are merely
    # getting the total combined time to transfer data
    combined_physical_index = -1
    try:
        combined_physical_index = copy_queries.index('Combined_Physical_Bandwidth')
        copy_queries[combined_physical_index] = 'Elapsed'  
    except:
        # Nothing to do, so don't worry about it
        pass

    # If the only query is Compress_Size, we do not need to get offsets
    if len(copy_queries) == 1 and copy_queries[0] == 'Compress_Size':
        pass
    else:
        with open(file_names[0]) as fp:
            line = fp.readline()
            while line.find(copy_queries[0]) == -1:
                line = fp.readline()
            line_list = line.split()
            for x in copy_queries:
                if x != 'Compress_Size':
                    offsets.append(line_list.index(x))
    
    # Finally just put the offset of Compress_Size if we need to
    if set_compress_size_offset:
        offsets.append(1)


def get_size_in_mb(file_size):
    numeric_portion = file_size[:-1]
    size_factor = file_size[len(file_size) - 1]

    if size_factor == 'K':
        return float(numeric_portion)/1024
    elif size_factor == 'M':
        return float(numeric_portion)
    elif size_factor == 'G':
        return float(numeric_portion)*1024
    else:
        # Assumed size_factor == 'T'
        return float(numeric_portion)*(1024**2)
    


# Specific getting_data function for passes input
def getting_data_runs(base_dir, queries, chart_titles, y_labels, threads, grab):
    offsets = []
    data_points = []
    std_devs = []
    std_errs = []
    run_datapoints = []
    runs = 0 
    
    # Getting the total number of runs per input test 
    runs = get_total_num_runs(base_dir)
    
    # Getting offsets of points of interest
    get_offsets(base_dir, offsets, queries)
    
    # Initializing data points, std_devs, std_errs
    data_points = [[] for l in range(len(queries))]
    std_devs = [[] for l in range(len(queries))]
    std_errs = [[] for l in range(len(queries))]
    
    for t in threads:
        input_file += '_run_'
        
        #initializing current runs data sets
        run_datapoints = [[] for l in range(len(queries))]
            
        for r in range(1,runs+1):
            # Getting current input based on run #
            current_input = input_file
            current_input += str(r) + '_threads_' + str(t) + '.txt'
            input_fp = open(current_input, 'r')
            if len(queries) == 1 and queries[0] == 'Compress_Size':
                # If the only query is Compress_Size we do not need to
                # get to actual XDD output just ZFS list output
                pass
            else:
                # Parsing out XDD normal header info
                parse_test_case_header(input_fp, queries)
            line = input_fp.readline()
            line_list = line.split()
            xdd_file_offset = 0
            # Getting data points of interest for this run
            for x in xrange(len(queries)):
                if queries[x] == 'Compress_Size':
                    # If query is Compress_Size, we just need to read to the
                    # end of the file and grab the amount of data
                    if len(line_list) > 13:
                        line_list = correct_xdd_output(line_list, xdd_file_offset)
                    if 'MOUNTPOINT' not in line_list:
                        jump_to_zfs_list_input(input_fp)
                    line = input_fp.readline()
                    line_list = line.split()
                    # Removing size of file from ZFS list output
                    line_list[offsets[x]] = line_list[offsets[x]][:-1]
                    run_datapoints[x].append(float(line_list[offsets[x]]))
                    continue
                elif queries[x] == 'Physical_Bandwidth':
                    # If the query is Physical_Bandwidth, we must also grab
                    # the actual file size at end of file and do the conversion
                    # division
                    if len(line_list) > 13:
                        line_list = correct_xdd_output(line_list, xdd_file_offset)
                    elapsed_time = line_list[offsets[x]]
                    last_pos = jump_to_zfs_list_input(input_fp)
                    line = input_fp.readline()
                    line_list = line.split()
                    # Removing size of file from ZFS list output
                    run_datapoints[x] = get_size_in_mb(line_list[1])/float(elapsed_time)
                    input_fp.seek(last_pos)
                elif queries[x] == 'Combined_Physical_Bandwidth':
                    # fp_offset_line_list = [last_pos, line_list]
                    fp_offset_line_list = jump_to_xdd_combined_input(input_fp)
                    if len(line_list) > 13:
                        line_list = correct_xdd_output(line_list, xdd_file_offset)
                    elapsed_time = line_list[offsets[x]]
                    jump_to_zfs_list_input(input_fp)
                    line = input_fp.readline()
                    line_list = line.split()
                    # Removing size of file from ZFS list output
                    run_datapoints[x] = get_size_in_mb(line_list[1])/float(elapsed_time)
                    input_fp.seek(fp_offset_line_list[0])
                    line_list = fp_offset_line_list[1]
                elif queries[x] == 'Combined_Bandwidth':
                    # If the query is Combined_Bandwidth, we just need to skip to
                    # the combined XDD output line
                    # fp_offset_line_list = [last_pos, line_list]
                    fp_offset_line_list = jump_to_xdd_combined_input(input_fp)
                    last_pos = fp_offset_line_list[0]
                    line_list = fp_offset_line_list[1]
                    if len(line_list) > 13:
                        line_list = correct_xdd_output(line_list, xdd_file_offset)
                    run_datapoints[x].append(float(line_list[offsets[x]]))
                    input_fp.seek(last_pos)
                elif queries[x] == 'Combined_CPU':
                    # If the query is Combined_CPU, we just need to skip to
                    # the combined XDD output line
                    # fp_offset_line_list = [last_pos, line_list]
                    fp_offset_line_list = jump_to_xdd_combined_input(input_fp)
                    last_pos = fp_offset_line_list[0]
                    line_list = fp_offset_line_list[1]
                    if len(line_list) > 13:
                        line_list = correct_xdd_output(line_list, xdd_file_offset)
                    run_datapoints[x].append(float(line_list[offsets[x]]))
                    input_fp.seek(last_pos)
                else:   
                    if len(line_list) > 13:
                        line_list = correct_xdd_output(line_list, xdd_file_offset)
                    run_datapoints[x].append(float(line_list[offsets[x]]))
            xdd_file_offset += 1        
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
            std_errs[x].append(numpy.std(run_datapoints[x])/(runs**0.5))
    
    # Writing out all output to output file
    base_dir_list = base_dir.split('/')
    output_file_name = base_dir_list[len(base_dir_list) - 1]
    output_file_name += '_data.txt'
    write_output_file(output_file_name, queries, threads, data_points, \
                      std_devs, std_errs, chart_titles, y_labels)




# Specific getting_data function for passes input
def getting_data_passes(base_dir, queries, chart_titles, y_labels, threads, grab):
    offsets = []
    data_points = []
    std_devs = []
    std_errs = []
    run_datapoints = []
    num_passes = 0
    
    # getting number of passes
    num_passes = get_total_num_passes(base_dir)
    
    # Getting offsets of points of interest
    get_offsets(base_dir, offsets, queries)
    
    # Initializing data points, std_devs, std_errs
    data_points = [[] for l in range(len(queries))]
    std_devs = [[] for l in range(len(queries))]
    std_errs = [[] for l in range(len(queries))]
    
    for t in threads:
        # for each thread we will get the median, standard
        # deviations, and standard error for all queries
        input_file = base_dir + '/'
        path_split = base_dir.split('/')
        input_file += path_split[-1]
        input_file += '_passes'
        
        #initializing current runs data sets
        run_datapoints = [[] for l in range(len(queries))]
        
        current_input = input_file
        current_input += '_threads_' + str(t) + '.txt'
        input_fp = open(current_input, 'r')
        if len(queries) == 1 and queries[0] == 'Compress_Size':
            # If the only query is Compress_Size we do not need to
            # get to actual XDD output just ZFS list output
            pass
        else:
            # Parsing out XDD normal header info
            parse_test_case_header(input_fp, queries)
        # Getting all datapoints
        for p in xrange(num_passes):
            line = input_fp.readline()
            line_list = line.split()
            # Getting data points of interest for this run
            xdd_file_offset = 0
            for x in xrange(len(queries)):
                if queries[x] == 'Compress_Size':
                    # If query is Compress_Size, we just need to read to the
                    # end of the file and grab the amount of data
                    if len(line_list) > 13:
                        line_list = correct_xdd_output(line_list, xdd_file_offset)
                    if 'MOUNTPOINT' not in line_list:
                        jump_to_zfs_list_input(input_fp)
                    line = input_fp.readline()
                    line_list = line.split()
                    # Removing size of file from ZFS list output
                    line_list[offsets[x]] = line_list[offsets[x]][:-1]
                    run_datapoints[x].append(float(line_list[offsets[x]]))
                    continue
                elif queries[x] == 'Physical_Bandwidth':
                    # If the query is Physical_Bandwidth, we must also grab
                    # the actual file size at end of file and do the conversion
                    # division
                    if len(line_list) > 13:
                        line_list = correct_xdd_output(line_list, xdd_file_offset)
                    elapsed_time = line_list[offsets[x]]
                    last_pos = jump_to_zfs_list_input(input_fp)
                    line = input_fp.readline()
                    line_list = line.split()
                    run_datapoints[x] = get_size_in_mb(line_list[1])/float(elapsed_time)
                    input_fp.seek(last_pos)
                elif queries[x] == 'Combined_Physical_Bandwidth':
                    # fp_offset_line_list = [last_pos, line_list]
                    fp_offset_line_list = jump_to_xdd_combined_input(input_fp)
                    if len(line_list) > 13:
                        line_list = correct_xdd_output(line_list, xdd_file_offset)
                    elapsed_time = line_list[offsets[x]]
                    jump_to_zfs_list_input(input_fp)
                    line = input_fp.readline()
                    line_list = line.split()
                    # Removing size of file from ZFS list output
                    run_datapoints[x] = get_size_in_mb(line_list[1])/float(elapsed_time)
                    input_fp.seek(fp_offset_line_list[0])
                    line_list = fp_offset_line_list[1]
                elif queries[x] == 'Combined_Bandwidth':
                    # If the query is Combined_Bandwidth, we just need to skip to
                    # the combined XDD output line
                    # fp_offset_line_list = [last_pos, line_list]
                    fp_offset_line_list = jump_to_xdd_combined_input(input_fp)
                    last_pos = fp_offset_line_list[0]
                    line_list = fp_offset_line_list[1]
                    if len(line_list) > 13:
                        line_list = correct_xdd_output(line_list, xdd_file_offset)
                    run_datapoints[x].append(float(line_list[offsets[x]]))
                    input_fp.seek(last_pos)
                elif queries[x] == 'Combined_CPU':
                    # If the query is Combined_CPU, we just need to skip to
                    # the combined XDD output line
                    # fp_offset_line_list = [last_pos, line_list]
                    fp_offset_line_list = jump_to_xdd_combined_input(input_fp)
                    last_pos = fp_offset_line_list[0]
                    line_list = fp_offset_line_list[1]
                    if len(line_list) > 13:
                        line_list = correct_xdd_output(line_list, xdd_file_offset)
                    run_datapoints[x].append(float(line_list[offsets[x]]))
                    input_fp.seek(last_pos)
                else:        
                    if len(line_list) > 13:
                        line_list = correct_xdd_output(line_list, xdd_file_offset)
                    run_datapoints[x].append(float(line_list[offsets[x]]))
            xdd_file_offset += 1        
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
            std_errs[x].append(numpy.std(run_datapoints[x])/(num_passes**0.5))
    
    # Writing out all output to output file
    base_dir_list = base_dir.split('/')
    output_file_name = base_dir_list[len(base_dir_list) - 1]
    output_file_name += '_data.txt'
    write_output_file(output_file_name, queries, threads, data_points, \
                      std_devs, std_errs, chart_titles, y_labels)



# Specific getting_data function for num_files input
def getting_data_num_files(base_dir, queries, chart_titles, y_labels, threads, grab, xval):
    num_files = []
    offsets = []
    std_devs = []
    std_errs = []
    run_data_points = []
    input_fp = open('/dev/null','r')

    # Getting the total number of files written in the tests
    get_num_files(num_files, base_dir)
    
    # Getting offsets of points of interest
    get_offsets(base_dir, offsets, queries)
   
    # Initializing data points, std_devs, std_errs
    data_points = [[] for l in range(len(queries))]
    std_devs = [[] for l in range(len(queries))]
    std_errs = [[] for l in range(len(queries))]

    # Now setting up all the lists for the number of files
    for x in range(len(queries)):
        for y in xrange(len(num_files)):
            data_points[x].append([])
            std_devs[x].append([])
            std_errs[x].append([])

    # Now accessing is done by data_points[0][0].append()
    for num_file_offset in xrange(len(num_files)):
        for t in threads:
            run_datapoints = [[] for l in xrange(len(queries))]
            input_fp.close()
            # for each thread we will get the grab value, standard
            # deviations, and standard error for all queries
            input_file = base_dir + '/'
            path_split = base_dir.split('/')
            input_file += path_split[-1]
            input_file += '_passes_threads_' + str(t)
            input_file += '_num_files_' + str(num_files[num_file_offset]) + '.txt'
            input_fp = open(input_file, 'r')
            if len(queries) == 1 and queries[0] == 'Compress_Size':
                # If the only query is Compress_Size we do not need to
                # get to actual XDD output just ZFS list output
                pass
            else:
                # Parsing out XDD normal header info
                parse_test_case_header(input_fp, queries)
            
            xdd_file_offset = 0
            for y in range(num_files[num_file_offset]):
                line = input_fp.readline()
                line_list = line.split()
                # Getting data points of interest for this run
                for x in xrange(len(queries)):
                    if queries[x] == 'Compress_Size':
                        # If query is Compress_Size, we just need to read to the
                        # end of the file and grab the amount of data
                        if len(line_list) > 13:
                            line_list = correct_xdd_output(line_list, xdd_file_offset)
                        if 'MOUNTPOINT' not in line_list:
                            last_pos = jump_to_zfs_list_input(input_fp)
                            line = input_fp.readline()
                            line_list = line.split()
                            # Removing size of file from ZFS list output
                            line_list[offsets[x]] = line_list[offsets[x]][:-1]
                            run_datapoints[x].append(float(line_list[offsets[x]]))
                            input_fp.seek(last_pos)
                            continue
                    elif queries[x] == 'Physical_Bandwidth':
                        # If the query is Physical_Bandwidth, we must also grab
                        # the actual file size at end of file and do the conversion
                        # division
                        if len(line_list) > 13:
                            line_list = correct_xdd_output(line_list, xdd_file_offset)
                        elapsed_time = line_list[offsets[x]]
                        last_pos = jump_to_zfs_list_input(input_fp)
                        line = input_fp.readline()
                        line_list = line.split()
                        run_datapoints[x].append(get_size_in_mb(line_list[1])/float(elapsed_time))
                        input_fp.seek(last_pos)
                    elif queries[x] == 'Combined_Physical_Bandwidth':
                        # fp_offset_line_list = [last_pos, line_list]
                        fp_offset_line_list = jump_to_xdd_combined_input(input_fp)
                        if len(line_list) > 13:
                            line_list = correct_xdd_output(line_list, xdd_file_offset)
                        elapsed_time = line_list[offsets[x]]
                        jump_to_zfs_list_input(input_fp)
                        line = input_fp.readline()
                        line_list = line.split()
                        # Removing size of file from ZFS list output
                        run_datapoints[x] = get_size_in_mb(line_list[1])/float(elapsed_time)
                        input_fp.seek(fp_offset_line_list[0])
                        line_list = fp_offset_line_list[1]
                    elif queries[x] == 'Combined_Bandwidth':
                        # If the query is Combined_Bandwidth, we just need to skip to
                        # the combined XDD output line
                        # fp_offset_line_list = [last_pos, line_list]
                        fp_offset_line_list = jump_to_xdd_combined_input(input_fp)
                        last_pos = fp_offset_line_list[0]
                        line_list = fp_offset_line_list[1]
                        if len(line_list) > 13:
                            line_list = correct_xdd_output(line_list, xdd_file_offset)
                        run_datapoints[x].append(float(line_list[offsets[x]]))
                        input_fp.seek(last_pos)
                    elif queries[x] == 'Combined_CPU':
                        # If the query is Combined_CPU, we just need to skip to
                        # the combined XDD output line
                        # fp_offset_line_list = [last_pos, line_list]
                        fp_offset_line_list = jump_to_xdd_combined_input(input_fp)
                        last_pos = fp_offset_line_list[0]
                        line_list = fp_offset_line_list[1]
                        if len(line_list) > 13:
                            line_list = correct_xdd_output(line_list, xdd_file_offset)
                        run_datapoints[x].append(float(line_list[offsets[x]]))
                        input_fp.seek(last_pos)
                    else:    
                        new_line_list = []
                        # Hacky work around to fix extra tab inserted
                        # in XDD output for certain PASS'es. Our only
                        # hope of fixing this error is if the tab appears
                        # In a floating point number...
                        # Also need to address TARGET_PASS being split...
                        if len(line_list) > 13:
                            line_list = correct_xdd_output(line_list, xdd_file_offset)
                        run_datapoints[x].append(float(line_list[offsets[x]]))
                xdd_file_offset += 1

            for x in xrange(len(queries)):  
                if grab == 'mean':
                    # Getting mean of run values
                    data_points[x][num_file_offset].append(numpy.mean(run_datapoints[x]))
                if grab == 'median':
                    # Getting median of run values
                    data_points[x][num_file_offset].append(numpy.median(run_datapoints[x]))
                if grab == 'min':
                    # Getting min of run values
                    data_points[x][num_file_offset].append(numpy.min(run_datapoints[x]))
                if grab == 'max':
                    # Getting max of run values
                    data_points[x][num_file_offset].append(numpy.max(run_datapoints[x]))
                # Getting Standard Deviation for Data Points
                std_devs[x][num_file_offset].append(numpy.std(run_datapoints[x]))
                # Getting Standard Error for Data Points
                std_errs[x][num_file_offset].append(numpy.std(run_datapoints[x])/(num_files[num_file_offset]**0.5))
            
            input_fp.close()

    # Writing out all output to output file
    base_dir_list = base_dir.split('/')
    output_file_name = base_dir_list[len(base_dir_list) - 1]
    output_file_name += '_data.txt'
    if xval != None:
        if xval == 'threads':
            write_output_file_num_files_for_threads(output_file_name, queries, threads, data_points, \
                                                    std_devs, std_errs, chart_titles, y_labels, num_files)
        elif xval == 'files':
            write_output_file_num_files_for_files(output_file_name, queries, threads, data_points, \
                                                  std_devs, std_errs, chart_titles, y_labels, num_files)
    else:
        # Default is x-values are the number of I/O threads
        write_output_file_num_files_for_threads(output_file_name, queries, threads, data_points, \
                                                std_devs, std_errs, chart_titles, y_labels, num_files)


def getting_data(base_dir, queries, chart_titles, y_labels, threads, grab, xval):
    offsets = []
    data_points = []
    std_devs = []
    std_errs = []
    run_datapoints = []
    num_passes = 0

    if is_num_files(base_dir):
        getting_data_num_files(base_dir, queries, chart_titles, y_labels, threads, grab, xval) 
    elif is_passes_xdd_data(base_dir):
        getting_data_passes(base_dir, queries, chart_titles, y_labels, threads, grab)
    else:
        getting_data_runs(base_dir, queries, chart_titles, y_labels, threads, grab)



def create_bulk_plot_files(plot_dir, xdd_dir, grab, xval):    
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
                     grab,
                     xval)
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
    parser.add_argument('-x', '--xval', type=str,
                         help='Can define what value to use for x-values valid options are (threads,files)')
    
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
    
    # Checking to make sure that if the x values are specified that it is set
    # to threads or files
    if args.xval is not None:
        if args.xval != 'threads' and args.xval != 'files':
            print 'The only allowed x-vals are threads or files'
            parser.print_help()
            sys.exit(0)

    if args.bulk is not None:
        bulk_list = args.bulk.split(',')
        plot_dir = bulk_list[0].rstrip('/')
        xdd_dir = bulk_list[1].rstrip('/')
        create_bulk_plot_files(plot_dir, xdd_dir, grab, args.xval)
    else:
        dir_path = args.directory.rstrip('/')
        get_threads(threads, dir_path)
        parse_input_file(args.input_file, queries, chart_titles, y_labels)
        getting_data(dir_path, 
                     queries, 
                     chart_titles, 
                     y_labels, 
                     threads,
                     grab,
                     args.xval) 

if __name__ == "__main__":
    main()
