% REDUCEBLOCKS  Vulcan block CSV -> un-rotated, re-blocked, compact file.
%
% Export from Vulcan with block selection ore_type >= 0 and NO grade filter.
% This script: reads the needed columns, drops air, undoes the model
% rotation, aggregates to AGG x 10 m blocks with tonnage-weighted grade,
% and writes blocks_small.csv (grid indices, tonnes, grade).

inFiles = {'output_1.csv','output_2.csv','output_3.csv','output_4.csv', ...
           'output_5.csv','output_6.csv','output_7.csv'};   % <-- the seven Z slices
outFile = 'blocks_small.csv';
AGG     = 2;                       % 2 -> 20 m blocks, 3 -> 30 m
ROT_DEG = 30;                      % model bearing, confirmed from centroid pattern

%% Read header from the first file, locate columns
[fid, msg] = fopen(inFiles{1}, 'r');
if fid < 0, error('Cannot open %s: %s', inFiles{1}, msg); end
hdr = strtrim(strsplit(strtrim(fgetl(fid)), ','));
fclose(fid);
want = {'centroid_x','centroid_y','centroid_z','au_ppm','density','ore_type','rock_type'};
[tf, pos] = ismember(want, hdr);
if ~all(tf), error('Missing columns: %s', strjoin(want(~tf), ', ')); end

opts = delimitedTextImportOptions('NumVariables', numel(hdr));
opts.VariableNames = matlab.lang.makeValidName(hdr);
opts.DataLines = [5 Inf];
opts.Delimiter = ',';
opts.VariableTypes = repmat({'double'}, 1, numel(hdr));
opts.SelectedVariableNames = opts.VariableNames(pos);
opts.ImportErrorRule = 'omitrow';
opts.MissingRule = 'fill';

B = table();
for f = 1:numel(inFiles)
    fprintf('Reading %s ...\n', inFiles{f});
    T = readtable(inFiles{f}, opts);
    fprintf('  %d rows\n', height(T));
    B = [B; T]; %#ok<AGROW>
end
B = B(B.ore_type >= 0, :);
B.tonnes = 1000 * B.density;
fprintf('  %d rock blocks, %.0f Mt, z %.0f-%.0f\n', height(B), sum(B.tonnes)/1e6, min(B.centroid_z), max(B.centroid_z));

%% Undo rotation about the model corner, then grid at 10 m
c = cosd(-ROT_DEG); s = sind(-ROT_DEG);
x0 = min(B.centroid_x); y0 = min(B.centroid_y);
u = c*(B.centroid_x - x0) - s*(B.centroid_y - y0);
v = s*(B.centroid_x - x0) + c*(B.centroid_y - y0);
u = u - min(u); v = v - min(v);
ix = round(u / 10); iy = round(v / 10);
iz = round((max(B.centroid_z) - B.centroid_z) / 10);        % 0 = top bench

% Sanity: after un-rotation the 10 m lattice should be exact
fprintf('  lattice residual (m): u %.3f  v %.3f  (should be ~0)\n', ...
    max(abs(u - 10*ix)), max(abs(v - 10*iy)));

%% Re-block to AGG x 10 m, tonnage-weighted grade
IX = floor(ix / AGG); IY = floor(iy / AGG); IZ = floor(iz / AGG);
[key, ~, g] = unique([IX IY IZ], 'rows');
tonnes = accumarray(g, B.tonnes);
metal  = accumarray(g, B.tonnes .* B.au_ppm);
sulph  = accumarray(g, B.tonnes .* (B.ore_type == 1)) ./ tonnes;   % sulphide fraction, for ARD later

out = table(key(:,1), key(:,2), key(:,3), tonnes, metal ./ tonnes, sulph, ...
    'VariableNames', {'ix','iy','iz','tonnes','grade','sulphide_frac'});
writetable(out, outFile);
d = dir(outFile);
fprintf('Wrote %s: %d blocks at %d m, %.0f Mt (%.0f MB)\n', outFile, height(out), 10*AGG, sum(tonnes)/1e6, d.bytes/1e6);