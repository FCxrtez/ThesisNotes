The issue stage’s purpose is to receive the decoded instructions and issue them to the various functional units. Furthermore the issue stage keeps track of all issued instructions, the functional unit status and receives the write-back data from the execute stage.
When it receives the write-back data does this mean that there is no WB stage? same hw as issue stage? In diagram Scoreboard is both in issue and WB.

It contains the CPU's register file. You can roughly divide the execution in four parts:
    1. issue
    2. read operands
    3. execute
    4. write-back
The issue stage handles step one, two and four.

When the issue stage gets a new decoded instruction it checks whether the required functional unit is free or will be free in the next cycle. Then it checks if its source operands are available and if no other, currently issued, instruction will write the same destination register. Furthermore it keeps track that no unresolved branch gets issued. The latter is mainly needed to simplify hardware design. By only allowing one branch we can easily back-track if we later find-out that we’ve mis-predicted on it.
By ensuring that the scoreboard only allows one instruction to write a certain destination register it easies the design of the forwarding path significantly. The scoreboard has a combinatorial circuit which outputs the status of all 32 destination register together with what functional unit will produce the outcome. This signal is called rd_clobber.

The issuing of instructions happen in-order, that means order of program flow is naturally maintained. What can happen out-of-order is the write-back of each functional unit. 
This scheme allows the functional units to operate in complete independence of the issue logic. They can return different transactions in different order. The scoreboard will know where to put them as long as the corresponding ID is signaled alongside the result. This scheme even allows the functional unit to buffer results and process them entirely out-of-order if it makes sense to them
