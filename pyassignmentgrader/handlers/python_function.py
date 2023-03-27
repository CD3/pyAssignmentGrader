import pyparsing as pp
import inspect
import functools


def wrap_func_in_generator(func,*args,**kwargs):
    yield func(*args,**kwargs)
    return
    

class PythonFunctionHandler:
    class parsers:
        module_name = pp.Word(pp.alphas+"_"+".",pp.alphas+pp.nums+"_"+".")
        function_name = pp.Word(pp.alphas+"_",pp.alphas+pp.nums+"_")
        function_signature = pp.QuotedString(quote_char="(",end_quote_char=")")
        

        function_specification = module_name("module_name") + ":" + function_name("function_name") + pp.Optional(function_signature)("function_signature")
    
    def make_import_statement(self,parse_results):
        code = f"from {parse_results['module_name']} import {parse_results['function_name']}"
        return code
    
    def __init__(self,function_spec,ctx={}):
        self.function = None
        self.function_spec = function_spec if function_spec.endswith(")") else function_spec+"()"
        self.ctx = ctx # context object
        function_spec = self.function_spec.format(**self.ctx)
        try:
            parse_results = self.parsers.function_specification.parse_string(function_spec,parse_all=True)
        except Exception as e:
            raise RuntimeError(f"Could not parse the function specification '{self.function_spec}': {e}")
        self.module_name = parse_results["module_name"]
        self.function_name = parse_results["function_name"]
        self.function_args = parse_results["function_signature"] if "function_signature" in parse_results else None
        try:
            exec(self.make_import_statement(parse_results))
        except Exception:
            raise RuntimeError(f"Could not import function '{self.function_name}' from module '{self.module_name}'.")
        # We need to bind any user-defined arguments to the function call here.
        self.function = eval(f"functools.partial({parse_results['function_name']},{self.function_args})")
        self.function_signature = inspect.signature(self.function)
        self.current_generator = None

    def call(self,*args,**kwargs):
        return self.function(*args,**kwargs)

    def yield_next(self,*args,**kwargs):
        if self.current_generator is None:
            if inspect.isgeneratorfunction(self.function):
                self.current_generator = self.function(*args,**kwargs)
            else:
                self.current_generator = wrap_func_in_generator(self.function,*args,**kwargs)
        try:
            return next(self.current_generator)
        except StopIteration as e:
            self.current_generator = None
            return None




        
