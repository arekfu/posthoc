import magic
from xmlresult import XMLResult

class SourceError(Exception):
    pass

class DataSource:
    def __init__(self, item):
        self.default_options = {
                'batch_num': 'last',
                'divide_by_bin': True,
                }
        try:
            self.setup_from_xml(item)
        except IndexError:
            self.setup_from_txt(item)

    def setup_from_xml(self, item):
        try:
            file_name = item[0]
            score_name = item[1]
        except IndexError:
            raise SourceError

        self.kwargs = self.default_options.copy()

        try:
            self.kwargs.update(item[2])
        except IndexError:
            pass

        with magic.Magic() as m:
            magic_id = m.id_filename(file_name)

            if 'XML' in magic_id:
                xml_result = XMLResult(file_name)
                self.result = xml_result.mean_result(
                        score_name,
                        batch_num=self.kwargs['batch_num'],
                        divide_by_bin=self.kwargs['divide_by_bin']
                        )
            else:
                raise Exception('for the moment we only accept XML input')

        del self.kwargs['batch_num']
        del self.kwargs['divide_by_bin']

    def setup_from_txt(self, item):
        pass

