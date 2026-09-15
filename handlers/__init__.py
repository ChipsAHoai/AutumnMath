from . import arithmetic, fraction, alg, mix, multi_alg, parens, decimal_multi_div, slope, ruler, cm_ruler
from . import common_multiples

registry = {
    "lcm": common_multiples.lcm,
    "gcf": common_multiples.gcf,
    "+": arithmetic.plus,
    "-": arithmetic.minus,
    "x": arithmetic.times,
    "*": arithmetic.times,
    "÷": arithmetic.divide,
    "fraction": fraction.generate,
    "alg": alg.generate,
    "mix": mix.generate,
    "multi_alg": multi_alg.generate,
    "parens": parens.generate,
    "decimal_multi_div": decimal_multi_div.generate,
    "slope": slope.generate,
    "ruler": ruler.generate,
    "cm_ruler": cm_ruler.generate,
}
