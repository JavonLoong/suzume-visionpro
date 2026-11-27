using System;
using System.Globalization;
using System.Text;

// Hardware-independent protocol. A GATT write is transport success, never motion completion.
public sealed class DoorBleProtocol
{
    public enum Phase { Disconnected, Query, Ready, AwaitAck, Moving, Fault }
    public Phase State { get; private set; }
    public bool CanAct => State==Phase.Ready && Calibrated && Position>=500 && Position<=2500;
    public bool Calibrated { get; private set; }
    public int Position { get; private set; } = -1;
    public int Target { get; private set; } = -1;
    public int PendingSequence { get; private set; }
    public char PendingCommand { get; private set; }
    public string Status { get; private set; } = "disconnected";
    public event Action<string> Transmit;
    readonly StringBuilder buffer=new StringBuilder();
    int nextSequence=1;
    double deadline;

    public void Disconnect()
    {
        buffer.Clear();PendingSequence=0;PendingCommand='\0';nextSequence=1;
        Calibrated=false;Position=Target=-1;State=Phase.Disconnected;Status="disconnected";
    }
    public void Connected(double now)
    {
        Disconnect();State=Phase.Query;Status="query";Send('Q',now);
    }
    void Send(char command,double now)
    {
        if(nextSequence>65535) { Fail("sequence_exhausted");return; }
        PendingSequence=nextSequence++;PendingCommand=command;deadline=now+2.5;
        // Query phase is installed by Connected; action phase by Request before invoking transport.
        Transmit?.Invoke(command+","+PendingSequence.ToString(CultureInfo.InvariantCulture)+"\n");
    }
    public bool Request(char command,double now)
    {
        if(!CanAct || (command!='O' && command!='C'))return false;
        State=Phase.AwaitAck;Status=command=='O'?"opening_request":"closing_request";
        Send(command,now);return State!=Phase.Fault;
    }
    public void Tick(double now)
    {
        if((State==Phase.Query||State==Phase.AwaitAck||State==Phase.Moving)&&now>=deadline)Fail("timeout");
    }
    public void TransportError(string reason) { Fail(reason); }
    void Fail(string reason)
    {
        State=Phase.Fault;Status=reason;Calibrated=false;PendingSequence=0;PendingCommand='\0';buffer.Clear();
    }
    static bool Number(string text,out int value)=>int.TryParse(text,NumberStyles.None,CultureInfo.InvariantCulture,out value);
    static bool PositionValue(string text,out int value)=>int.TryParse(text,NumberStyles.AllowLeadingSign,CultureInfo.InvariantCulture,out value);
    public void Feed(string bytes,double now)
    {
        // A delayed notification must not revive an expired request just because
        // the transport drains its event queue before Update calls Tick.
        Tick(now);
        if(State==Phase.Disconnected||State==Phase.Fault||bytes==null)return;
        foreach(char c in bytes)
        {
            if(c=='\n') { var line=buffer.ToString();buffer.Clear();Parse(line,now);if(State==Phase.Fault)return; }
            else if(c<32||c>126||buffer.Length>=128) { Fail("BAD");return; }
            else buffer.Append(c);
        }
    }
    void Parse(string line,double now)
    {
        var p=line.Split(',');
        if(p.Length<3||p[0].Length!=1||!Number(p[1],out int sequence)||sequence>65535) { Fail("BAD");return; }
        char kind=p[0][0];
        if(kind=='E'&&p.Length==3&&sequence==0) { Fail(p[2]);return; }
        // Ignore stale characteristic values, unmatched requests and completed duplicates.
        if(sequence==0||sequence!=PendingSequence)return;
        if(kind=='E'&&p.Length==3) { Fail(p[2]);return; }
        if(kind=='R'&&State==Phase.Query&&p.Length==4&&Number(p[2],out int calibrated)&&
           (calibrated==0||calibrated==1)&&PositionValue(p[3],out int position))
        {
            Position=position;Calibrated=calibrated==1;PendingSequence=0;PendingCommand='\0';
            if(!Calibrated) { Fail("UNCAL");return; }
            if(position<500||position>2500) { Fail("READ");return; }
            State=Phase.Ready;Status="ready";return;
        }
        if(kind=='A'&&p.Length==3&&State==Phase.AwaitAck&&PositionValue(p[2],out int target)&&target>=500&&target<=2500)
        {
            Target=target;State=Phase.Moving;Status=PendingCommand=='O'?"opening":"closing";deadline=now+12;return;
        }
        if(kind=='A'&&p.Length==3&&State==Phase.Moving&&PositionValue(p[2],out int duplicateTarget)&&duplicateTarget==Target)return;
        if(kind=='D'&&p.Length==3&&State==Phase.Moving&&PositionValue(p[2],out int actual)&&actual>=500&&actual<=2500)
        {
            Position=actual;Status=PendingCommand=='O'?"opened":"closed";PendingSequence=0;PendingCommand='\0';State=Phase.Ready;return;
        }
        // In particular, D before A must not claim completion.
        Fail("BAD");
    }
}

// Requires both buttons released after entering Browse, regaining tracking or finishing a request.
public sealed class DoorBleButtonGate
{
    bool armed;
    public char Step(bool eligible,bool a,bool b)
    {
        if(!eligible) { armed=false;return '\0'; }
        if(!a&&!b) { armed=true;return '\0'; }
        if(!armed)return '\0';
        armed=false;
        if(a&&b)return '\0';
        return a?'O':'C';
    }
    public void Reset() { armed=false; }
}
