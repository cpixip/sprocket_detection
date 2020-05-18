# sprocket_detection

A simple and sufficiently fast Python script to detect the sprocket position of a Super-8 frame. 

The script relies on some assumptions in order to detect the sprocket effectively; if these assumptions are violated too much, the detection will fail. In this case, the input image is left unchanged. Some more elaborate approaches based for example on Hough-transforms migth be needed for general cases.

Assumptions:

1. The edges of the sprocket should run along the horizontal and vertical image coordinate axis. This requirement is used in a simplified evidence accumulation. If this assumption is violated, the algorithm will still work up to a limit.
2. It is previous known where the sprocket location might be approximately expected. Only this region-of-interest is searched in the algorithm. 
3. The sprocket area is brighter than the surrounding film stock. The algorithm works best with color-reversal film for which it was developed, but good results were also obtained with clear film stock.
4. The algorithm works at most pixel-precise. In order to get good results, the input images should have a fine enough resolution.

The basic idea is to detect in the region-of-interest horizonally running edges. The most prominent ones are corresponding to the location of the sprockets. The edges are found in a two step procedure: 
A. Locate strong edges in a coarse way by starting from the other boundaries of the frame searching towards the middle of the frame.
- Use the found coordinates to arrive at an estimate for the center of the sprocket.
- Search for the edge boundaries starting from the found center of the sprocket.
- Estimate from the found inner edges a more precise guess for the sprocket center.

More information can be obtained by the following <a href="https://forums.kinograph.cc/t/simple-super-8-sprocket-registration/1683?u=cpixip">KINOGRAPH forum thread</a>.
