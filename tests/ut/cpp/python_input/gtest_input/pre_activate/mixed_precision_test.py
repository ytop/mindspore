# Copyright 2020 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
from mindspore.ops import operations as P
from mindspore.ops import Primitive

tuple_getitem = Primitive('tuple_getitem')
depend = Primitive('depend')
addn = P.AddN()
add = P.TensorAdd()
sub = P.Sub()
mul = P.Mul()
max_pool = P.MaxPoolWithArgmax(pad_mode="same", window=3, stride=2)
make_tuple = Primitive('make_tuple')
cast = Primitive('Cast')


class FnDict:
    def __init__(self):
        self.fnDict = {}

    def __call__(self, fn):
        self.fnDict[fn.__name__] = fn

    def __getitem__(self, name):
        return self.fnDict[name]


def test_insert_cast_op_for_single_output(tag):
    fns = FnDict()

    @fns
    def before(x, y):
        res = add(x, y)
        return res

    @fns
    def after(x, y):
        new_x = cast(x)
        new_y = cast(y)
        res = add(new_x, new_y)
        res = cast(res)
        return make_tuple(res)

    return fns[tag]


def test_insert_cast_op_for_single_output_new(tag):
    fns = FnDict()

    @fns
    def before(x, y):
        res = add(x, y)
        output = make_tuple(res)
        return output

    @fns
    def after(x, y):
        new_x = cast(x)
        new_y = cast(y)
        res = add(new_x, new_y)
        output = cast(res)
        new_output = make_tuple(output)
        return make_tuple(new_output)

    return fns[tag]


def test_eliminate_cast_op(tag):
    fns = FnDict()

    @fns
    def before(x, y):
        sum = addn((x, y))
        sum_depend = depend(sum, addn((x, y)))
        diff = sub(x, y)
        res = mul(sum_depend, diff)
        return res

    @fns
    def after1(x, y):
        new_x_sum = cast(x)
        new_y_sum = cast(y)
        sum = addn(new_x_sum, new_y_sum)
        sum_cast = cast(sum)
        new_x_depend = cast(x)
        new_y_depend = cast(y)
        sum_depend = addn(new_x_depend, new_y_depend)
        sum_depend_cast = cast(sum_depend)
        depend_between_cast = depend(sum_cast, sum_depend_cast)
        depend_cast = cast(depend_between_cast)
        new_x_diff = cast(x)
        new_y_diff = cast(y)
        diff = sub(new_x_diff, new_y_diff)
        diff_cast1 = cast(diff)
        diff_cast2 = cast(diff_cast1)
        res = mul(depend_cast, diff_cast2)
        output = cast(res)
        new_output = make_tuple(output)
        return new_output

    @fns
    def after2(x, y):
        new_x_sum = cast(x)
        new_y_sum = cast(y)
        sum = addn(new_x_sum, new_y_sum)
        new_x_depend = cast(x)
        new_y_depend = cast(y)
        sum_depend = addn(new_x_depend, new_y_depend)
        sum_depend_cast = cast(sum_depend)
        depend_between_cast = depend(sum, sum_depend_cast)
        new_x_diff = cast(x)
        new_y_diff = cast(y)
        diff = sub(new_x_diff, new_y_diff)
        res = mul(depend_between_cast, diff)
        output = cast(res)
        new_output = make_tuple(output)
        return new_output

    return fns[tag]


def test_insert_cast_op_for_multiple_output(tag):
    fns = FnDict()

    @fns
    def before(x):
        output = max_pool(x)
        return tuple_getitem(output, 0)

    @fns
    def after(x):
        new_x = cast(x)
        output = max_pool(new_x)
        cast0 = cast(tuple_getitem(output, 0))
        cast1 = cast(tuple_getitem(output, 1))
        res = make_tuple(cast0, cast1)
        return make_tuple(tuple_getitem(res, 0))

    return fns[tag]


def test_eliminate_cast_new(tag):
    fns = FnDict()

    @fns
    def before(x, y):
        sum = add(x, y)
        res = sub(sum, y)
        output = make_tuple(res)
        return output

    @fns
    def after1(x, y):
        new_x_sum = cast(x)
        new_y_sum = cast(y)
        new_y_sum2 = cast(y)
        sum = add(new_x_sum, new_y_sum)
        sum_5to4 = cast(sum)
        sum_4to5 = cast(sum_5to4)
        res = sub(sum_4to5, new_y_sum2)
        output = cast(res)
        new_output = make_tuple(output)
        return new_output

    @fns
    def after2(x, y):
        new_x_sum = cast(x)
        new_y_sum = cast(y)
        new_y_diff = cast(y)
        sum = add(new_x_sum, new_y_sum)
        res = sub(sum, new_y_diff)
        output = cast(res)
        new_output = make_tuple(output)
        return new_output

    return fns[tag]
