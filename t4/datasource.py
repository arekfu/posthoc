# coding: utf-8

from xmlresult import XMLResult, TXTResult
from collections import Mapping

class SourceError(Exception):
    pass

class DataSource:
    def __init__(self, item):
        self.default_xml_options = {
                'batch_num': 'last',
                'divide_by_bin': True,
                }
        try:
            self.init_from_xml(item)
        except IndexError:
            self.init_from_txt(item)

    def init_from_xml(self, item):
        """Initialize the data source from an XML file.

        If item is supposed to represent XML input, it must be of the form
           (file_name, score_name[, kwargs])
        where file_name and score_name are strings and kwargs is an optional
        dictionary of options. We test for these properties.
        """

        try:
            file_name = item[0]
            score_name = item[1]
        except IndexError:
            raise SourceError

        if not isinstance(file_name, basestring) or not isinstance(score_name, basestring):
            raise SourceError

        self.kwargs = self.default_xml_options.copy()

        try:
            options = item[2]
        except IndexError:
            pass
        if not isinstance(options, Mapping):
            raise SourceError
        self.kwargs.update(options)

        # Here we assume file_name is a valid, well-formed T4 output file
        xml_result = XMLResult(file_name)
        self.result = xml_result.mean_result(
                score_name,
                batch_num=self.kwargs['batch_num'],
                divide_by_bin=self.kwargs['divide_by_bin']
                )

        del self.kwargs['batch_num']
        del self.kwargs['divide_by_bin']

    def init_from_txt(self, item):
        """Initialize the data source from a text file.
        """

        try:
            file_name = item[0]
        except IndexError:
            if not isinstance(iter, basestring):
                raise SourceError
            else:
                file_name = item

        try:
            options = item[1]
        except IndexError:
            pass

        # Here we assume file_name is a valid, well-formed T4 output file
        xml_result = TXTResult(file_name)
        self.result = xml_result.mean_result(**options)
