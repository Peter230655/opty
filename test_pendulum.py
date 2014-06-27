import numpy as np
from sympy import symbols, Function, Matrix, simplify

import pendulum


def test_discrete_symbols():
    t = symbols('t')
    v, x = symbols('v, x', cls=Function)
    f = symbols('f', cls=Function)

    v = v(t)
    x = x(t)
    f = f(t)

    states = [v, x]
    specified = [f]

    current_states, previous_states, current_specified, interval = \
        pendulum.discrete_symbols(states, specified)

    xi, vi, xp, vp, fi, h = symbols('xi, vi, xp, vp, fi, h')

    assert current_states[0] is vi
    assert current_states[1] is xi
    assert previous_states[0] is vp
    assert previous_states[1] is xp
    assert current_specified[0] is fi
    assert interval is h


def test_build_constraint():

    t = symbols('t')
    v, x = symbols('v, x', cls=Function)
    m, c, k = symbols('m, c, k')
    f = symbols('f', cls=Function)

    v = v(t)
    x = x(t)
    f = f(t)

    states = [v, x]

    mass_matrix = Matrix([[m, 0], [0, 1]])
    forcing_vector = Matrix([-c * v - k * x + f, v])

    constraint = pendulum.build_constraint(mass_matrix, forcing_vector, states)

    expected = Matrix([m * v.diff() + c * v + k * x + f,
                       x.diff() - v])

    assert simplify(constraint - expected) == Matrix([0, 0])


def test_discretize():

    t, h = symbols('t, h')
    v, x = symbols('v, x', cls=Function)
    m, c, k = symbols('m, c, k')
    f = symbols('f', cls=Function)

    v = v(t)
    x = x(t)
    f = f(t)

    states = [v, x]
    specified = [f]

    eoms = Matrix([m * v.diff() + c * v + k * x + f,
                   x.diff() - v])

    discrete_eoms = pendulum.discretize(eoms, states, specified, h)

    xi, vi, xp, vp, fi = symbols('xi, vi, xp, vp, fi')

    expected = Matrix([m * (vi - vp) / h + c * vi + k * xi + fi,
                       (xi - xp) / h - vi])

    assert simplify(discrete_eoms - expected) == Matrix([0, 0])


def test_general_constraint_function():

    t, h = symbols('t, h')
    v, x = symbols('v, x', cls=Function)
    m, c, k = symbols('m, c, k')
    f = symbols('f', cls=Function)

    v = v(t)
    x = x(t)
    f = f(t)

    states = [v, x]
    specified = [f]

    xi, vi, xp, vp, fi = symbols('xi, vi, xp, vp, fi')

    eom_vector = Matrix([m * (vi - vp) / h + c * vi + k * xi + fi,
                         (xi - xp) / h - vi])

    constrain = pendulum.general_constraint_function(eom_vector, states, specified,
                                             [m, c, k])

    state_values = np.array([[1, 2, 3, 4],
                             [5, 6, 7, 8]])
    specified_values = np.array([2, 2, 2, 2])
    constant_values = np.array([1.0, 2.0, 3.0])
    m, c, k = constant_values
    h = 0.01

    result = constrain(state_values, specified_values, constant_values, h)

    expected_dynamic = np.zeros(3)
    expected_kinematic = np.zeros(3)

    for i in [1, 2, 3]:

        vi, xi = state_values[:, i]
        vp, xp = state_values[:, i - 1]
        fi = specified_values[i]

        expected_dynamic[i - 1] = m * (vi - vp) / h + c * vi + k * xi + fi
        expected_kinematic[i - 1] = (xi - xp) / h - vi

    expected = np.hstack((expected_dynamic, expected_kinematic))

    np.testing.assert_allclose(result, expected)


def test_constraint_function():

    t, h = symbols('t, h')
    v, x = symbols('v, x', cls=Function)
    m, c, k = symbols('m, c, k')
    f = symbols('f', cls=Function)

    v = v(t)
    x = x(t)
    f = f(t)

    states = [v, x]
    specified = [f]

    xi, vi, xp, vp, fi = symbols('xi, vi, xp, vp, fi')

    eom_vector = Matrix([m * (vi - vp) / h + c * vi + k * xi + fi,
                         (xi - xp) / h - vi])

    general_constrain = pendulum.general_constraint(eom_vector, states, specified,
                                                     [m, c, k])

    num_time_steps = 4
    num_states = 2
    interval_value = 0.01
    fixed_constants = {m: 1.0, c: 2.0}
    fixed_specified = {fi: np.array([2, 2, 2, 2])}

    # you pass in the general constraint function with all the fixed values
    constrain = pendulum.constraint_func(general_constrain,
            num_time_steps, num_states, interval_value, [m, c, k], [fi], fixed_constants,
            fixed_specified)

    free = np.array([1, 2, 3, 4, 5, 6, 7, 8, 3.0])

    result = constrain(free)

    expected_dynamic = np.zeros(3)
    expected_kinematic = np.zeros(3)

    state_values = np.array([[1, 2, 3, 4],
                             [5, 6, 7, 8]])
    specified_values = np.array([2, 2, 2, 2])
    constant_values = np.array([1.0, 2.0, 3.0])
    m, c, k = constant_values
    h = interval_value

    for i in [1, 2, 3]:

        vi, xi = state_values[:, i]
        vp, xp = state_values[:, i - 1]
        fi = specified_values[i]

        expected_dynamic[i - 1] = m * (vi - vp) / h + c * vi + k * xi + fi
        expected_kinematic[i - 1] = (xi - xp) / h - vi

    expected = np.hstack((expected_dynamic, expected_kinematic))

    np.testing.assert_allclose(result, expected)



def test_constraint_gradient():
    """

    scipy_slsqp needs a function that takes the free parameters (x) and returns an array

    shape(len(constraint vector), len(free parameters))
    shape(N - 1, ...)

    First I need a function that evaluates the non-zero entries of the
    gradient matrix.

    eom_vector.jacobian(every variable in expressions except h)

    This will return a num_states x num_variable matrix where each column is df/dvar.

    These columns will populate a sparse matrix that is




    """
    t, h = symbols('t, h')
    v, x = symbols('v, x', cls=Function)
    m, c, k = symbols('m, c, k')
    f = symbols('f', cls=Function)

    v = v(t)
    x = x(t)
    f = f(t)

    states = [v, x]
    specified = [f]

    xi, vi, xp, vp, fi = symbols('xi, vi, xp, vp, fi')

    eom_vector = Matrix([m * (vi - vp) / h + c * vi + k * xi + fi,
                         (xi - xp) / h - vi])

    constrain = pendulum.constraint_gradient_function(eom_vector, states, specified,
                                                      [m, c, k])

    state_values = np.array([[1, 2, 3, 4],
                             [5, 6, 7, 8]])
    specified_values = np.array([2, 2, 2, 2])
    constant_values = np.array([1.0, 2.0, 3.0])
    m, c, k = constant_values
    h = 0.01

    result = constrain(state_values, specified_values, constant_values, h)

    expected_dynamic = np.zeros(3)
    expected_kinematic = np.zeros(3)

    for i in [1, 2, 3]:

        vi, xi = state_values[:, i]
        vp, xp = state_values[:, i - 1]
        fi = specified_values[i]

        expected_dynamic[i - 1] = m * (vi - vp) / h + c * vi + k * xi + fi
        expected_kinematic[i - 1] = (xi - xp) / h - vi

    expected = np.hstack((expected_dynamic, expected_kinematic))

    np.testing.assert_allclose(result, expected)