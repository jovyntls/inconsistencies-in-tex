2306.00005
MANUAL: [1,2,3] high similarity, only text spacing issues. 2>3>1
MANUAL: [-2] low similarity, almost entirely different content
EVALUATION: CW/SSIM and SIFT follow the 2>3>1 order. CW/SSIM are suitably high in similarity, but SIFT is lower than it should be.
1	0.749	0.793	0.680	0.568
2	0.886	0.921	0.672	0.672
3	0.849	0.904	0.544	0.647
it's weird that SIFT is so high for [-3] since it's visually similar to [1-3]
-1	0.859	0.898	0.494	0.629
-2	0.490	0.454	0.386	0.439
-3	0.580	0.401	0.193	0.882

2306.00006
MANUAL: [1,2,3] text spacing, 1>2>3
MANUAL: [-1] very high similarity
MANUAL: [-2] identical features translated, but has missing content
MANUAL: [-3] completely different
EVALUATION: [-1] all are correctly high; [-1,-2,-3] all have the right order (-1>-2>-3)
SIFT: seems to overly weight the box in [-2], resulting in too high values for [2]. ranges from 0.44-0.55 for questionable text spacing
SSIM: maybe 0.6-0.8 for acceptable? overweights [-2] at 0.786
CWSSIM: maybe 0.6-0.8 for acceptable 
-1	0.992	0.994	0.918	0.906
-2	0.786	0.703	0.592	0.671
-3	0.638	0.542	0.350	0.505
1	0.803	0.838	0.882	0.542
2	0.619	0.613	0.350	0.425
3	0.527	0.507	0.380	0.443

2306.00007
MANUAL: all pages text spacing, with [-3] being the most prominent. all acceptable
EVALUATION: it does highlight [-3] as the most prominent. 
SIFT: ranges from 0.6-0.75 for the acceptable text spacing, 0.45 for the lowest
SSIM: ranges from 0.83-0.94 for the acceptable text spacing, 0.7 for the lowest
CWSSIM: ranges from 0.87-0.96 for the acceptable text spacing, 0.71 for the lowest
ORB: anomalous 0.916 for [1], no idea why
-1	0.842	0.894	0.500	0.608
-2	0.917	0.943	0.642	0.672
-3	0.700	0.715	0.434	0.442
1	0.939	0.958	0.916	0.749
2	0.826	0.871	0.510	0.598
3	0.858	0.908	0.550	0.632

2306.00076
MANUAL: [1-3] acceptable tho 3 is questionable. 1>2>3
MANUAL: [-1,-2] bad. [-3] text spacing, but not acceptable
SIFT: [-1] way too high. text spacing range 0.53-0.6
ORB: [-1,-2] is correct. text spacing 0.45-0.69
SSIM: [-1,-2] too high. text spacing range 0.42-0.62. [-3, 3] is within that range but unacceptable
CWSSIM: [-1] is too high. text spacing 0.4-0.6. [3] is wrongly within that range, [-3] is correctly out
-1	0.901	0.635	0.183	0.816
-2	0.628	0.406	0.222	0.450
-3	0.492	0.381	0.452	0.535
1	0.617	0.605	0.690	0.566
2	0.425	0.403	0.520	0.559
3	0.487	0.451	0.488	0.599
hypothesis: counterbalance with ORB?
I think I should have divided by max for SIFT. dividing by min will overweight features that exist and ignore missing features
