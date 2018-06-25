def main():

input_file = args.input_file

parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_file', type=str,
                         help='Plot configuration file',
                         required=True)
    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(0)

    # Getting vals
    line = fp.readline()
    vals = line.split()
    total_datasets = int(vals[0])
    poi = int(vals[1])
    line = fp.readline()
    x_title = line.replace('# x-title ','')
    x_title = x_title.replace('\n','')
    line = fp.readline()
    x_vals = [int(s) for s in line.split() if s.isdigit()]

    #This is the list of lists
    all_trace = [[] for l in xrange(total_datasets)]

    for x in xrange(total_datasets):
        line = fp.readline()
        line_split = line.split()
        chart_type = line_split(1)
        if chart_type == 'line':
            for y in xrange(poi):
                all_trace[x].append(go.Scatter(x = x_vals))
        elif chart_type == 'bar':
            for y in  xrange(poi):
                all_trace[x].append(go.Bar(x = x_vals))
        else:
            exit(1)

        for y in xrange(poi):
            line = fp.readline()
	    line_split2 = line.split()
	    y_title = line.replace('# y-title', '')
	    # Should the x_title above be line.replace('\n', '')?
	    y_title = line.replace('\n', '')
	    line = fp.readline()
	    through_vals = [int(s) for s in line.split() if s.isdigit()]
	    # Now take those values (above)  and plot them.
	    if chart_type == 'line':
		for y in xrange(poi):
		    all_trace[y].append(go.Scatter(y = through_vals)
	    elif chart_type == 'bar':
		for y in xrange(poi):
		    all_trace[y].append(go.Bar(y = through_vals)
	    fp.readline()
	    line = fp.readline()
	    dev_vals = [int(s) for s in line.split() if s.isdigit()]
	    #Then plot based on chart_type?
	    #Do the same thing for STDERR?
	    fp.readline()
	    line = fp.readline()
	    err_vals = [int(s) for s in line.split() if s.isdigit()]
	    #Then plot based on chart_type?
            # Grab everything out of the file and plot it all. Put all 3 points of interest in the same graph and plot it. 
            

