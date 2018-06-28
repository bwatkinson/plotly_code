import sys
import argparse
import string

def parse_point_of_interest_file(poi_file, input_files):
    poi = ''
    with open(poi_file, 'r') as fp:
        for line in fp:
            if '.txt' in line:
                input_files.append(line)
            elif '#' not in line:
                poi = line    
    return poi

def parse_data_labels(input_data_files, data_labels_file, data_labels):
    chart_title = ''
    with open(data_labels_file, 'r') as fp:
        # Getting rid of comments at top of the file
        line = fp.readline()
        while '#' in line:
            line = fp.readline()
        chart_title = line
        for x in xrange(len(input_data_files)):
            # Now just reading to end of file
            line = fp.readline()
            # Removing Comments
            while '#' in line:
                line = fp.readline()
            data_labels.append(line)
    return chart_title

def write_new_output_file(point_of_interest, 
                          chart_title,
                          x_title, 
                          x_vals, 
                          data_labels,
                          new_data_labels,
                          y_vals):

    total_vals = 0
    total_datasets = 0
    total_y_vals_per_dataset = 0

    fp = open('all_' + point_of_interest + '_data.txt', 'w')
    
    total_datasets = len(new_data_labels)
    total_y_vals_per_dataset = len(y_vals[0])

    # Writing out header information that is static
    fp.write(str(total_datasets) + ' ' + 
             str(total_y_vals_per_dataset) + 
             ' ALL\n')
    fp.write(x_title)
    fp.write(' '.join(map(str,x_vals[0])) + '\n')

    for label, val in zip(new_data_labels, y_vals):
        fp.write('# ' + chart_title.rstrip() + ',' + label[0].split(',')[2]) 
        for label_val, val_val in zip(label, val):
            fp.write(label_val)
            fp.write(val_val)
    fp.close()


def combine_files(input_data_files, point_of_interest, data_label_file):
    data_labels = []
    x_title = ''
    x_vals = []
    label_offset = 0

    
    chart_title = parse_data_labels(input_data_files, 
                                    data_label_file,
                                    data_labels)

    # The number of lables much match the number of input files
    if len(data_labels) != len(input_data_files):
        print 'ERROR: There was not enough labels provided in data label file'
        print 'Exiting...'
        return

    if chart_title == '':
        print 'Error Parsing Data Labels File'
        print 'Exiting...'
        return

    new_data_labels = [[] for x in xrange(len(data_labels))]
    y_vals = [[] for x in xrange(len(data_labels))]

    for curr_file in input_data_files:
        with open(curr_file, 'r') as fp:
            line = fp.readline()
            while 'x-title' not in line:
                line = fp.readline()
            if x_title == '':
                # Only need to set x-title once
                x_title = line
            # Grabbing x-values
            line = fp.readline()
            x_vals.append([int(s) for s in line.split() if s.isdigit()])
            # Checking to make sure that x-values are all the same
            # From every input file
            if len(set(x_vals[0]).intersection(x_vals[len(x_vals)-1])) != len(x_vals[0]):
                # x-values are differnt, so just stop
                print 'ERORR: x-values differ between files'
                print 'Exiting...'
                return
            while True:
                # Justing finding all the points of interest in rest of file
                if '' == line:
                    break
                line = fp.readline()
                if point_of_interest in line:
                    if 'y-title' in line:
                        # Updating title to new label
                        line_list = line.split(',')
                        line_list[len(line_list) - 1] = data_labels[label_offset]
                        line_str = string.join(line_list,',')
                        new_data_labels[label_offset].append(line_str)
                        # Now getting y values
                        line = fp.readline()
                        y_vals[label_offset].append(line)
                    elif 'STDERR' in line:
                        # Updating title to new label
                        line_list = line.split(',')
                        line_list[len(line_list) - 1] = data_labels[label_offset]
                        line_str = string.join(line_list,',')
                        new_data_labels[label_offset].append(line_str)
                        # Now getting y values
                        line = fp.readline()
                        y_vals[label_offset].append(line)
                    elif 'STDDEV' in line:
                        # Updating title to new label
                        line_list = line.split(',')
                        line_list[len(line_list) - 1] = data_labels[label_offset]
                        line_str = string.join(line_list,',')
                        new_data_labels[label_offset].append(line_str)
                        # Now getting y values
                        line = fp.readline()
                        y_vals[label_offset].append(line)
                    else:
                        pass # Ignore input value (must be chart type line)
        label_offset += 1;

    # Now writing out combined data output file
    write_new_output_file(point_of_interest, 
                          chart_title,
                          x_title, 
                          x_vals, 
                          data_labels,
                          new_data_labels,
                          y_vals)


def main():
    input_files = []

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--point_of_interest_file', type=str,
                        help='File that list files to combine and point of interest',
                        required=True)
    parser.add_argument('-l', '--data_labels_file', type=str,
                        help='File containing chart title and line labels',
                        required=True)


    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(0)
    
    poi_file = args.point_of_interest_file
    poi = parse_point_of_interest_file(poi_file, input_files)
    poi = poi.rstrip()
    input_files = [x.rstrip() for x in input_files]
    combine_files(input_files, poi, args.data_labels_file)

if __name__ == '__main__':
    main()
