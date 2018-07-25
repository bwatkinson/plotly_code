import sys
import argparse
import string

def parse_point_of_interest_file(poi_file, input_files):
    poi = []
    with open(poi_file, 'r') as fp:
        for line in fp:
            if '.txt' in line and '#' not in line:
                input_files.append(line)
            elif '#' not in line:
                poi.append(line)    
    return poi

def parse_data_labels(input_data_files, data_labels_file, data_labels):
    chart_title = ''
    with open(data_labels_file, 'r') as fp:
        # Getting rid of comments at top of the file
        line = fp.readline()
        while '#' in line:
            line = fp.readline()
        chart_title = line
        # Now just reading to end of file
        line = fp.readline()
        while line != '':
            # Removing Comments
            while '#' in line:
                line = fp.readline()
            data_labels.append(line)
            line = fp.readline()    
    return chart_title

def write_new_output_file(chart_title,
                          x_titles, 
                          x_vals, 
                          data_labels,
                          new_data_labels,
                          y_vals):


    total_vals = 0
    total_datasets = 0
    total_y_vals_per_dataset = 0


    fp = open('all_combined_data.txt', 'w')
    
    total_datasets = len(new_data_labels)
    total_y_vals_per_dataset = len(y_vals[0])

    # Writing out header information that is static
    fp.write(str(total_datasets) + ' ' + 
             str(total_y_vals_per_dataset) + 
             ' ALL\n')

    for x_title, x_vals, label, val in zip(x_titles, x_vals, new_data_labels, y_vals):
        fp.write(x_title)
        fp.write(x_vals)
        fp.write('# ' + chart_title.rstrip() + ',' + label[0].split(',')[2]) 
        for label_val, val_val in zip(label, val):
            fp.write(label_val)
            fp.write(val_val)
    fp.close()


def combine_files(input_data_files, point_of_interest, data_label_file):
    data_labels = []
    x_vals = []
    
    chart_title = parse_data_labels(input_data_files, 
                                    data_label_file,
                                    data_labels)


    # The number of lables much match the number of poi search for in each file
    if len(data_labels) != (len(input_data_files) * len(point_of_interest)):
        print 'ERROR: There was not enough labels provided in data label file'
        print 'Exiting...'
        return

    if chart_title == '':
        print 'Error Parsing Data Labels File'
        print 'Exiting...'
        return

    x_titles = []
    new_data_labels = [[] for x in xrange(len(data_labels))]
    y_vals = [[] for x in xrange(len(data_labels))]
    
    label_offset = 0
    for curr_file in input_data_files:
        curr_poi_offset = 0
        for curr_poi in point_of_interest:
            with open(curr_file, 'r') as fp:
                line = fp.readline()
                while True:
                    while line != '' and 'x-title' not in line:
                        line = fp.readline()
                
                    if line == '':
                        break
                
                    if line.split(',')[2] != curr_poi:
                        # Current x-title not a point of interest, so continue
                        line = fp.readline()
                        continue
                
                    # Creating new x-title
                    line_list = line.split(',')
                    line_list[len(line_list) - 1] = data_labels[label_offset]
                    line_str = string.join(line_list,',')
                    x_titles.append(line_str)
                    # Grabbing x-values
                    line = fp.readline()
                    if chart_title.split(',')[0] == 'bar':
                        x_vals_str_line = line.split(',')
                        # Removing old data label
                        x_vals_str_line.pop(len(x_vals_str_line) - 1)
                        curr_pos = 0
                        for x_str in x_vals_str_line:
                            x_vals_str_line[curr_pos] = x_str.strip()
                            curr_pos += 1
                        x_vals_str_new = ''
                        for x_values in x_vals_str_line:
                            if x_values != x_vals_str_line[len(x_vals_str_line) - 1]:
                                x_vals_str_new += x_values + ', '
                            else:
                                x_vals_str_new += x_values + ','
                        # Adding new label to the end
                        x_vals_str_new += data_labels[label_offset]
                        x_vals.append(x_vals_str_new)
                    elif chart_title.split(',')[0] == 'line':
                        x_vals_str_line = line.split()
                        # Removing old from end of list
                        x_vals_str_line[len(x_vals_str_line) - 1] = x_vals_str_line[len(x_vals_str_line) - 1].split(',')[0]
                        x_vals_str_new = ''
                        for x_values in x_vals_str_line:
                            if x_values != x_vals_str_line[len(x_vals_str_line) - 1]:
                                x_vals_str_new += x_values + ' '
                            else:
                                x_vals_str_new += x_values
                        # Adding new label to the end
                        x_vals_str_new += ',' + data_labels[label_offset] 
                        x_vals.append(x_vals_str_new)
        
                    
                    # Justing finding all the points of interest in rest of file
                    line = fp.readline()
                    while line != '' and 'x-title' not in line:
                        if curr_poi in line:
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
                        line = fp.readline()
                    curr_poi_offset += 1
                    label_offset += 1
    
    # Now writing out combined data output file
    write_new_output_file(chart_title,
                          x_titles, 
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
    input_files = [x.rstrip() for x in input_files]
    combine_files(input_files, poi, args.data_labels_file)

if __name__ == '__main__':
    main()
