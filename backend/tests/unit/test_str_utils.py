from lambdas.utils import str_utils


def test_convert_snake_to_camel_case():
    # assert str_utils.convert_snake_to_camel_case('abc') == 'abc'
    assert str_utils.convert_snake_to_camel_case('abc_def') == 'abcDef'
    assert str_utils.convert_snake_to_camel_case('abc_def_efg') == 'abcDefEfg'
    assert str_utils.convert_snake_to_camel_case('_abc') == 'Abc'
    assert str_utils.convert_snake_to_camel_case('abc_') == 'abc'
    assert str_utils.convert_snake_to_camel_case('_abc_def') == 'AbcDef'
    assert str_utils.convert_snake_to_camel_case('abc_def_') == 'abcDef'
