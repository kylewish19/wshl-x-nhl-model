import numpy as np
from scipy.stats import skellam,poisson
from wshlx_nhl.team_tie_shadow import resolved,regulation_scale

def test_tie_only_changes_even_boundary_total():
    h=np.array([3.]);a=np.array([3.])
    z=resolved(h,a,[0])
    assert np.isclose(z.home_ml.iloc[0],.5)
    assert np.isclose(z.home_minus15.iloc[0],skellam.sf(1,3,3))
    assert np.isclose(z.over55.iloc[0],poisson.sf(5,6))
    assert np.isclose(z.over65.iloc[0],poisson.sf(6,6)+poisson.pmf(3,3)**2)

def test_mean_preservation_and_nested_totals():
    for h,a in [(1.5,1.5),(3.,3.),(4.,2.)]:
        s=regulation_scale(h,a)
        assert 0<s<1
        assert np.isclose(s*(h+a)+skellam.pmf(0,s*h,s*a),h+a)
        p=resolved([h],[a],[0],preserve=True)
        assert p.over55.iloc[0]>=p.over65.iloc[0]
        assert p.apply(lambda x:x.between(0,1)).all().all()
