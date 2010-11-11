#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

import sys

def parse_cmdline_arguments(args):

    # defaults
    filename = None
    delimiter = "\t"
    outputs = []
    group = []

    # parsing and syntax check
    args = iter(args)
    while True:
        try:
            arg = args.next()
        except StopIteration:
            break
        if arg == '-f':
            # filename
            try:
                filename = args.next()
                continue
            except StopIteration:
                sys.exit("Missing argument for -f (filename)")
        if arg == '-d':
            # delimiter
            try:
                delimiter = args.next()
                continue
            except StopIteration:
                sys.exit("Missing argument for -d (field delimiter)")
        if arg == '-g':
            # group
            try:
                opt = args.next()
                try:
                    group.append(int(opt))
                    continue
                except ValueError:
                    sys.exit("Invalid argument for -g (must be numeric!)")
            except StopIteration:
                sys.exit("Missing argument for -g (column number)")
        if arg == '-o':
            # output
            try:
                opt = args.next()
                optargs = opt.split(',')

                if len(optargs) == 1:
                    if not optargs[0].isdigit():
                        sys.exit("Invalid argument for -o (must be numeric)")
                    outputs.append([int(optargs[0]), None]) # no aggregation
                    continue
                if len(optargs) == 2:
                    if not (optargs[0].isdigit() or (optargs[0] == '*' and optargs[1] == 'count')):
                        sys.exit("Invalid argument for -o (must be numeric or * for aggregate function count)")
                    outputs.append([optargs[0], optargs[1]]) # aggregation
                    continue
                sys.exit("Invalid number of arguments for option -o")
            except StopIteration:
                sys.exit("Missing argument for -o (column number [and aggregate function])")
        sys.exit("Unknown option: " + arg)

    # semantic check
    for output in outputs:
        if output[1] == None:
            if not output[0] in group:
                sys.exit("Non-aggregated output column (" + str(output[0]) + ") must be a group column")
        else:
            if output[0] in group:
                sys.exit("Aggregated output column (" + str(output[0]) + ") can't be a group column")

    return filename, delimiter, outputs, group

def get_data_source(filename):
    if filename != None and filename != "-":
        try:
            lines = open(filename, "r")
        except IOError:
            sys.exit("Unable to open " + filename + " for reading")
    else:
        lines = sys.stdin
    return lines

def collect_groups_with_order(lines, delimiter, group):
    groups = {}
    grouporder = []
    for line in lines:
        fields = line.rstrip().split(delimiter)
        key = []
        for position in group:
            try:
                key.append(fields[position])
            except IndexError:
                sys.exit("Column number " + str(position) +  " out of range")
        key = tuple(key)
        if groups.has_key(key):
            groups[key].append(fields)
        else:
            grouporder.append(key) # remember order of first occurances of groups
            groups[key] = [fields]
    return groups, grouporder

def output_groups(groups, grouporder, outputs, delimiter):
    for group in grouporder:
        output_line = []
        for output in outputs:
            if output[1] == None:
                output_line.append(groups[group][0][output[0]]) # no aggregation
            else:
                output_line.append(aggregate(groups[group], output[0], output[1])) # apply aggregate function
        print delimiter.join(output_line)

def aggregate(data, column, function):
    try:
        # most aggregate functions follow a simple map-reduce-pattern
        # some don't need map (like first and last) or map in their own way
        if function in ['sum', 'avg', 'max', 'min']:
            columndata = map(lambda row: row[int(column)], data)

        # make out aggregate function
        if function == 'sum':
            return str(reduce(lambda a, b: a + float(b), columndata, 0))
        if function == 'count':
            if column == '*':
                return str(len(data))
            else:
                # an empty string has the meaning that NULL has in SQL
                columndatafiltered = filter(lambda row: row != "", map(lambda row: row[int(column)], data))
                return str(len(columndatafiltered))
        if function == 'avg':
            return str(reduce(lambda a, b: a + float(b), columndata, 0) / len(columndata))
        if function == 'max':
            return str(reduce(lambda a, b: max(a,float(b)), columndata, float(columndata[0])))
        if function == 'min':
            return str(reduce(lambda a, b: min(a,float(b)), columndata, float(columndata[0])))
        if function == 'first':
            return data[0][int(column)]
        if function == 'last':
            return data[len(data)-1][int(column)]
        if function == 'median':
            columndatasorted = sorted(map(lambda row: float(row[int(column)]), data))
            if len(columndatasorted) % 2 == 0:
                # even: return average of the 2 elements in the middle
                return str((columndatasorted[len(columndatasorted) / 2 - 1] + columndatasorted[len(columndatasorted) / 2]) / 2)
            else:
                # odd: return element in the middle
                return str(columndatasorted[len(columndatasorted) / 2])
        sys.exit("Unknown aggregate function: " + function)
    except IndexError:
        sys.exit("Column number " + str(column) +  " out of range")
    except ValueError:
        sys.exit("Unable to cast input data of column " + str(column) + " to type required by aggregate function " + function)

if __name__ == "__main__":

    try:
        # parse command line options
        (filename, delimiter, outputs, group) = parse_cmdline_arguments(sys.argv[1:])

        # determine data source (file or stdin)
        lines = get_data_source(filename)

        # collect groups with order of first occurance
        groups, grouporder = collect_groups_with_order(lines, delimiter, group)

        # print groups
        output_groups(groups, grouporder, outputs, delimiter)

    except KeyboardInterrupt:
        sys.exit("Aborted by user")
