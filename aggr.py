#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

# aggr.py - aggr - aggregate CSV-data and print on the standard output
#
# Copyright (C) 2010, Stefan Schramm <mail@stefanschramm.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


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
        # interpret argument as output column
        outputs.append(arg)
        if arg.isdigit():
            # if it's only a number: group column
            group.append(int(arg))

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
            if output.isdigit():
                output_line.append(groups[group][0][int(output)]) # no aggregation
            else:
                output_line.append(aggregate(groups[group], output)) # apply aggregate function
        print delimiter.join(output_line)

def aggregate(data, output):
    
    try:
        function, column = output.split(":")
    except ValueError:
        sys.exit("Syntax error for output column: " + output)
        
    # special case: *,count
    if function == "count" and column == "*":
        return str(len(data))

    # following functions require column to be an integer
    if not column.isdigit():
        sys.exit("Column number for aggregate function must be numeric (or *, but only for count).")
    column = int(column);
        
    try:
        # most aggregate functions follow a simple map-reduce-pattern
        # some don't need map (like first and last) or map in their own way
        if function in ['sum', 'avg', 'max', 'min', 'count']:
            columndata = map(lambda row: row[column], data)

        # make out aggregate function
        if function == 'sum':
            return str(reduce(lambda a, b: a + float(b), columndata, 0))
        if function == 'count':
            # an empty string has the meaning that NULL has in SQL
            return str(len(filter(lambda row: row != "", columndata)))
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
            # here we're assuming that a numeric order is wanted!
            columndatasorted = sorted(map(lambda row: float(row[column]), data))
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
