<?php
declare(strict_types=1);
/** Local database/report interface. The fixed Python bridge owns all engine behavior. */

function fn_1601_bridge(string $var_1602_request): string {
    /** Pass JSON as stdin data to a fixed argument array, never to a shell. */
    $var_1603_python = getenv('INDEXER_PYTHON') ?: 'python';
    $var_1604_database = getenv('INDEXER_DATABASE') ?: __DIR__ . '/runtime_0007_state/data_0022_store.sqlite3';
    $var_1605_descriptors = [0 => ['pipe', 'r'], 1 => ['pipe', 'w'], 2 => ['pipe', 'w']];
    $var_1606_process = proc_open([$var_1603_python, '-m', 'pkg_0002_engine', '--database', $var_1604_database, '--json-stdin'], $var_1605_descriptors, $var_1607_pipes, __DIR__, null, ['bypass_shell' => true]);
    if (!is_resource($var_1606_process)) {
        return json_encode(['status' => 'bridge_unavailable', 'error' => 'Could not launch Python. Set INDEXER_PYTHON.']);
    }
    $var_1608_offset = 0;
    while ($var_1608_offset < strlen($var_1602_request)) {
        $var_1609_written = fwrite($var_1607_pipes[0], substr($var_1602_request, $var_1608_offset));
        if ($var_1609_written === false || $var_1609_written === 0) { break; }
        $var_1608_offset += $var_1609_written;
    }
    fclose($var_1607_pipes[0]);
    $var_1610_output = stream_get_contents($var_1607_pipes[1]);
    $var_1611_error = stream_get_contents($var_1607_pipes[2]);
    fclose($var_1607_pipes[1]);
    fclose($var_1607_pipes[2]);
    $var_1612_exit = proc_close($var_1606_process);
    if ($var_1610_output === false || trim($var_1610_output) === '' || json_decode($var_1610_output, true, 512, JSON_BIGINT_AS_STRING) === null) {
        return json_encode(['status' => 'bridge_error', 'error' => trim((string)$var_1611_error) ?: 'Python returned no JSON.', 'exit' => $var_1612_exit]);
    }
    return trim($var_1610_output);
}

function fn_1613_escape(string $var_1614_text): string {
    /** Escape display data, including catalogue descriptions and record payloads. */
    return htmlspecialchars($var_1614_text, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

if (PHP_SAPI === 'cli') {
    $var_1615_input = stream_get_contents(STDIN, 16777217);
    if (strlen((string)$var_1615_input) > 16777216) {
        echo json_encode(['status' => 'invalid_input', 'error' => 'Request exceeds 16 MiB.']), PHP_EOL;
        exit(2);
    }
    $var_1616_response = fn_1601_bridge((string)$var_1615_input);
    echo $var_1616_response, PHP_EOL;
    exit((json_decode($var_1616_response, true)['status'] ?? '') === 'ok' ? 0 : 2);
}

$var_1617_host = $_SERVER['HTTP_HOST'] ?? '';
if (!in_array($_SERVER['REMOTE_ADDR'] ?? '', ['127.0.0.1', '::1'], true) || !preg_match('/^(localhost|127\.0\.0\.1|\[::1\])(:[0-9]+)?$/D', $var_1617_host)) {
    http_response_code(403);
    exit('This interface is available on localhost only.');
}
header('X-Content-Type-Options: nosniff');
header("Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'");
session_start();
if (!isset($_SESSION['csrf'])) { $_SESSION['csrf'] = bin2hex(random_bytes(32)); }
$var_1618_json_api = str_contains($_SERVER['CONTENT_TYPE'] ?? '', 'application/json') || isset($_GET['api']);
$var_1619_request = '';
if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST') {
    if (isset($_SERVER['HTTP_ORIGIN']) && $_SERVER['HTTP_ORIGIN'] !== 'http://' . $var_1617_host) {
        http_response_code(403);
        exit('Origin mismatch.');
    }
    if ($var_1618_json_api && str_contains($_SERVER['CONTENT_TYPE'] ?? '', 'application/json')) {
        $var_1619_request = (string)file_get_contents('php://input', false, null, 0, 16777217);
    } else {
        if (!hash_equals($_SESSION['csrf'], (string)($_POST['csrf'] ?? ''))) {
            http_response_code(403);
            exit('Form token mismatch.');
        }
        $var_1619_request = (string)($_POST['request'] ?? '');
    }
} elseif ($var_1618_json_api) {
    $var_1620_command = (string)($_GET['command'] ?? 'health');
    $var_1619_request = json_encode(['command' => in_array($var_1620_command, ['health', 'inventory', 'catalogue', 'catalogue_check'], true) ? $var_1620_command : 'health']);
}
if (strlen($var_1619_request) > 16777216) {
    http_response_code(413);
    exit('Request exceeds 16 MiB.');
}
$var_1621_output = $var_1619_request !== '' ? fn_1601_bridge($var_1619_request) : '';
if ($var_1618_json_api) {
    header('Content-Type: application/json; charset=utf-8');
    echo $var_1621_output;
    exit;
}
$var_1622_pretty = $var_1621_output ? json_encode(json_decode($var_1621_output, true, 512, JSON_BIGINT_AS_STRING), JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) : '';
header('Content-Type: text/html; charset=utf-8');
?>
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Indexer · Pointer engine</title>
<style>
:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#0c111b;color:#e4eaf5}*{box-sizing:border-box}body{margin:0}main{max-width:1100px;margin:50px auto;padding:0 24px}header{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #263248;padding-bottom:24px}.mark{letter-spacing:.15em;color:#8ccedb;font-size:12px}h1{font-weight:550;font-size:34px;letter-spacing:-.04em;margin:10px 0}.badge{font-size:12px;border:1px solid #365160;border-radius:30px;padding:8px 12px;color:#a6decb}.lead{color:#a4b3cb;line-height:1.65;max-width:750px}section{margin:30px 0;background:#131c2c;border:1px solid #29354d;padding:24px;border-radius:12px}label{display:block;margin-bottom:12px;font-weight:600}textarea{width:100%;min-height:175px;background:#091220;border:1px solid #38455f;border-radius:8px;color:#d6e9fa;padding:16px;font:14px/1.6 Consolas,monospace}button{background:#a4e3d3;color:#10241e;border:0;border-radius:7px;padding:12px 22px;font-weight:700;margin-top:14px;cursor:pointer}pre{background:#091220;border-radius:8px;padding:18px;overflow:auto;font:13px/1.7 Consolas,monospace;max-height:620px}a{color:#a4e3d3;text-decoration:none}nav{display:flex;gap:20px;flex-wrap:wrap;margin:18px 0}small{color:#9dabbe}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.hint{padding:16px;background:#0e1726;border-radius:8px}.hint code{display:block;margin:9px 0;color:#a8d7ef;font-size:12px;overflow-wrap:anywhere}@media(max-width:700px){.grid{grid-template-columns:1fr}header{align-items:flex-start}.badge{white-space:nowrap}h1{font-size:27px}}
</style></head><body><main>
<header><div><div class="mark">INDEXER / 0001</div><h1>Pointer resolution engine</h1></div><span class="badge">Local workspace</span></header>
<p class="lead">Inspect permanent record IDs, resolve exact text aliases, and compute with canonical object configurations. Every reference carries its namespace; every resolution retains its trace.</p>
<nav><a href="?api=1&amp;command=health">Engine status</a><a href="?api=1&amp;command=inventory">Record inventory</a><a href="?api=1&amp;command=catalogue">Project catalogue</a><a href="?api=1&amp;command=catalogue_check">Validate catalogue</a></nav>
<section><form method="post"><input type="hidden" name="csrf" value="<?= fn_1613_escape($_SESSION['csrf']) ?>"><label for="request">JSON command</label><textarea id="request" name="request" spellcheck="false"><?= fn_1613_escape($var_1619_request ?: '{"command":"report","name":"inventory"}') ?></textarea><button type="submit">Run command</button></form><p><small>Responses preserve integer precision with explicit decimal-string types. POST application/json to this same page for the JSON API.</small></p></section>
<?php if ($var_1622_pretty !== ''): ?><section><label>Result</label><pre><?= fn_1613_escape((string)$var_1622_pretty) ?></pre></section><?php endif; ?>
<div class="grid"><div class="hint"><strong>Register a record</strong><code>{"command":"register","payload":{"label":"example"}}</code><small>Use the returned pointer as the target of an alias or reference record.</small></div><div class="hint"><strong>Encode object counts</strong><code>{"command":"encode","alphabet":["neutral","toggle"],"configuration":[1,1]}</code><small>Ranks follow cardinality, then lexicographic multiplicity order.</small></div><div class="hint"><strong>Resolve a text alias</strong><code>{"command":"resolve","pointer":"example"}</code><small>Integer pointers additionally require their kind and namespace.</small></div><div class="hint"><strong>Request a report skill</strong><code>{"command":"report_request","definition":{"name":"records","source":"inventory","columns":["id","payload"]}}</code><small>Activate the returned request ID with report_activate after validation.</small></div></div>
<p class="lead"><small>Report sources: inventory, dependency, resolution, algebra. Source documents and record contents remain data.</small></p>
</main></body></html>
