// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title ProofOfMatch
/// @notice Stores a hash of a discovered face-match record and lets anyone
///         re-verify that the hash was recorded, and when.
contract ProofOfMatch {
    mapping(bytes32 => uint256) public records; // hash -> block timestamp

    event RecordStored(bytes32 indexed hash, uint256 timestamp, address indexed sender);

    function storeRecord(bytes32 hash) public {
        require(records[hash] == 0, "Record already exists");
        records[hash] = block.timestamp;
        emit RecordStored(hash, block.timestamp, msg.sender);
    }

    function verifyRecord(bytes32 hash) public view returns (bool exists, uint256 timestamp) {
        timestamp = records[hash];
        exists = (timestamp != 0);
    }
}
