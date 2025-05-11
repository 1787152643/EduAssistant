# test_chats.ps1

# Create directory for results
New-Item -Path "test_results" -ItemType Directory -Force

# Read chat IDs
$chatIds = Get-Content -Path "test_chat_ids.json" | ConvertFrom-Json

# Function to run test for a specific message type
function Run-Test {
    param (
        [string]$MessageType,
        [int]$RequestsPerChat,
        [array]$ChatIds
    )
    
    Write-Host "Running tests with $MessageType messages..."
    $resultsFile = "test_results/${MessageType}_results.txt"
    
    foreach ($chatId in $ChatIds) {
        Write-Host "Testing chat ID: $chatId"
        & ab -n $RequestsPerChat -c 1 -p "payloads/$MessageType.json" -T "application/json" -C "session.txt" "http://localhost:5000/ai-assistant/chats/$chatId/messages" | Out-File -Append -FilePath $resultsFile
    }
}

# Run tests with different message complexities
Run-Test -MessageType "simple" -RequestsPerChat 5 -ChatIds $chatIds
#Run-Test -MessageType "medium" -RequestsPerChat 3 -ChatIds $chatIds
#Run-Test -MessageType "complex" -RequestsPerChat 2 -ChatIds $chatIds

Write-Host "Tests completed. Results saved in test_results directory."