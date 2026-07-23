<?php
include 'db.php';

$folder = __DIR__ . "/imports";
$files  = glob($folder . "/*.json");

if (!$files) {
    echo "No JSON files found in /imports folder.";
    exit;
}

foreach ($files as $file) {

    echo "<strong>Processing file:</strong> " . basename($file) . "<br>";

    $json = file_get_contents($file);
    $arr = json_decode($json, true);

    // JSON should be [ { ... }, { ... }, ... ]
    if (!is_array($arr)) {
        echo "Invalid JSON structure. Skipping.<br><br>";
        continue;
    }

    // -----------------------------
    // USER INSERT (once per file)
    // -----------------------------
    $filename = basename($file, ".json");
    $username = $conn->real_escape_string($filename);

    $sql_user = "INSERT INTO users (username) VALUES ('$username')";

    if (!$conn->query($sql_user)) {
        echo "User insert error: " . $conn->error . "<br>";
        continue;
    }

    $user_id = $conn->insert_id;
    echo "Created user: $username (ID: $user_id)<br>";

    // -----------------------------
    // LOOP THROUGH ALL CONVERSATIONS IN FILE
    // -----------------------------
    foreach ($arr as $index => $data) {

        echo "&nbsp;&nbsp;→ Processing conversation #" . ($index + 1) . "<br>";

        // -----------------------------
        // convo_id = filename + index
        // -----------------------------
        $convo_id = $conn->real_escape_string($filename . "_" . $index);

        // -----------------------------
        // CONVERSATION INSERT
        // -----------------------------
        $title = $conn->real_escape_string($data["title"] ?? "");

        $created_at = null;
        if (isset($data["create_time"])) {
            $created_at = date("Y-m-d H:i:s", (int)$data["create_time"]);
        }

        $sql_convo = "
            INSERT INTO conversations (convo_id, user_id, convo_title, created_at)
            VALUES ('$convo_id', '$user_id', '$title', '$created_at')
        ";

        if (!$conn->query($sql_convo)) {
            echo "&nbsp;&nbsp;Conversation insert error: " . $conn->error . "<br>";
            continue;
        }

        // -----------------------------
        // RAW FILE PATH INSERT
        // -----------------------------
        $file_path = "imports/" . basename($file);
        $file_path = $conn->real_escape_string($file_path);

        $sql_raw = "
            INSERT INTO raw_import (convo_id, file_path)
            VALUES ('$convo_id', '$file_path')
        ";

        if (!$conn->query($sql_raw)) {
            echo "&nbsp;&nbsp;RAW insert error: " . $conn->error . "<br>";
        }

        // -----------------------------
        // MESSAGE INSERT BLOCK
        // -----------------------------
        if (isset($data["mapping"]) && is_array($data["mapping"])) {

            $msgs = [];

            foreach ($data["mapping"] as $node) {

                if (!isset($node["message"])) continue;

                $msg = $node["message"];

                $role = $msg["author"]["role"] ?? "system";
                $content = $msg["content"] ?? null;
                $text = "";

                if ($content) {
                    $ctype = $content["content_type"] ?? "text";

                    // --------------------------------
                    // 1. Normal assistant/user text
                    // --------------------------------
                    if (isset($content["parts"])) {
                        $flat = [];
                        foreach ($content["parts"] as $p) {
                            $flat[] = is_array($p)
                                ? json_encode($p, JSON_UNESCAPED_UNICODE)
                                : $p;
                        }
                        $text = implode("\n", $flat);
                    }

                    // --------------------------------
                    // 2. Code messages
                    // --------------------------------
                    elseif ($ctype === "code" && isset($content["text"])) {
                        $text = $content["text"];
                    }

                    // --------------------------------
                    // 3. "Thoughts" content (role=tool)
                    // --------------------------------
                    elseif ($ctype === "thoughts" && isset($content["thoughts"])) {
                        $chunks = [];
                        foreach ($content["thoughts"] as $th) {
                            if (isset($th["summary"])) {
                                $chunks[] = $th["summary"];
                            }
                            if (isset($th["content"]) && $th["content"] !== "") {
                                $chunks[] = $th["content"];
                            }
                        }
                        $text = implode("\n", $chunks);
                    }

                    // --------------------------------
                    // 4. Reasoning recap
                    // --------------------------------
                    elseif ($ctype === "reasoning_recap" && isset($content["content"])) {
                        $text = $content["content"];
                    }

                    // --------------------------------
                    // 5. Fallback (capture everything)
                    // --------------------------------
                    else {
                        $text = json_encode($content, JSON_UNESCAPED_UNICODE);
                    }
                }

                // Timestamp
                $time = null;
                if (isset($msg["create_time"])) {
                    $time = date("Y-m-d H:i:s", (int)$msg["create_time"]);
                }

                $msgs[] = [
                    "role" => $role,
                    "msg"  => $text,
                    "time" => $time
                ];
            }

            // Sort by timestamp
            usort($msgs, function($a, $b) {
                return strtotime($a["time"]) <=> strtotime($b["time"]);
            });

            // Insert messages
            foreach ($msgs as $m) {
                $r = $conn->real_escape_string($m["role"]);
                $t = $conn->real_escape_string($m["msg"]);
                $d = $m["time"];

                $sql_msg = "
                    INSERT INTO messages (convo_id, role, message, created_at)
                    VALUES ('$convo_id', '$r', '$t', '$d')
                ";

                if (!$conn->query($sql_msg)) {
                    echo "&nbsp;&nbsp;Message insert error: " . $conn->error . "<br>";
                }
            }
        }

        echo "&nbsp;&nbsp;✓ Imported: $title<br>";
    }

    echo "File complete: " . basename($file) . "<br><br>";
}

echo "<strong>All imports completed.</strong>";
?>