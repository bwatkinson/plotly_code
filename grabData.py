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

    # This is the list of lists
    all_trace = [[] for l in xrange(total_datasets)]

    for x in xrange(total_datasets):
        line = fp.readline()
        line_split = line.split()
        chart_type = line_split(1)
        if chart_type == 'line':
            for y in xrange(poi):
		# Appending 'down'
                all_trace[x].append(go.Scatter(x = x_vals))
        elif chart_type == 'bar':
            for y in xrange(poi):
		# Appending 'down'
                all_trace[x].append(go.Bar(x = x_vals))
        else:
            exit(1)

        for y in xrange(poi):
            line = fp.readline()
	    line_split = line.split()
	    y_title = line.replace('# y-title', '')
	    y_title = y_title.replace('\n', '')
	    line = fp.readline()
	    throughput_vals = [int(s) for s in line.split() if s.isdigit()]
	    # Now take throughput_vals and plot them
	    if chart_type == 'line':
		for y in xrange(poi):
		    all_trace[x].append(go.Scatter(y = throughput_vals)
	    elif chart_type == 'bar':
		for y in xrange(poi):
		    all_trace[x].append(go.Bar(y = throughput_vals)
	    fp.readline()
	    line = fp.readline()
	    # Get standard deviation values
	    stdev_vals = [int(s) for s in line.split() if s.isdigit()]
	    if chart_type == 'bar':
		# Ignore standard deviation
		fp.readline()
		line = fp.readline()
		# Get standard error values
		err_vals = [int(s) for s in line.split() if s.isdigit()]
		# Plot error bars
		all_trace[x].error_y = dict(
		    type = 'data',
		    array = [err_vals],
		    visible = True
		)
	    elif chart_type == 'line':
		# Bounds for standard deviation
		upper_bound = go.Scatter(
		    name = 'Upper Bound',
		    x = x_vals,
		    y = throughput_vals + stdev_vals,
		    mode = 'lines',
		    marker = dict(color = '#444'),
		    line = dict(width = 0),
		    fillcolor = 'rgba(68, 68, 68, 0.3)',
		    fill = 'tonexty'
		)
		lower_bound = go.Scatter(
		    name = 'Lower Bound',
		    x = x_vals,
		    y = throughput_vals - stdev_vals,
		    mode = 'lines',
		    marker = dict(color = '#444'),
		    line = dict(width = 0)
		# Possibly add fillcolor and fill
		)
	        fp.readline()
	        line = fp.readline()
		# Is it necessary to get standard error values again?
	        err_vals = [int(s) for s in line.split() if s.isdigit()]
		# Plot error bars
		all_trace[x].error_y = dict(
                    type = 'data',
                    array = [err_vals],
                    visible = True
                )
	    # Now we have to put together a 2nd graph for CPU Percentage?
