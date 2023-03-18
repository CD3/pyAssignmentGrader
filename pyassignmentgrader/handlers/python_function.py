import pyparsing as pp


class PythonFunctionHandler:
    class parsers:
        module_name = pp.Word(pp.alphas+"_"+".",pp.alphas+pp.nums+"_"+".")
        function_name = pp.Word(pp.alphas+"_",pp.alphas+pp.nums+"_")
        function_signature = pp.QuotedString(quote_char="(",end_quote_char=")")

        function_specification = module_name("module_name") + ":" + function_name("function_name") + pp.Optional(function_signature)("function_signature")
    
    
    def __init__(self):
        pass
        
