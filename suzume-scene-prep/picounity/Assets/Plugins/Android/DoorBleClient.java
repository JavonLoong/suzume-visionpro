package com.suzume.door;

import android.Manifest;
import android.app.Activity;
import android.bluetooth.*;
import android.bluetooth.le.*;
import android.content.Context;
import android.content.pm.PackageManager;
import android.os.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.ConcurrentLinkedQueue;

/** Single GATT client; callback identity and generation prevent stale-session notifications. */
public final class DoorBleClient {
    static final UUID SERVICE=UUID.fromString("b4a10001-7d3b-4ad8-9f5e-529f9e3989a1");
    static final UUID REQUEST=UUID.fromString("b4a10002-7d3b-4ad8-9f5e-529f9e3989a1");
    static final UUID REPLY=UUID.fromString("b4a10003-7d3b-4ad8-9f5e-529f9e3989a1");
    static final UUID CCCD=UUID.fromString("00002902-0000-1000-8000-00805f9b34fb");
    final Activity activity;
    final Handler handler=new Handler(Looper.getMainLooper());
    final ConcurrentLinkedQueue<String> events=new ConcurrentLinkedQueue<>();
    BluetoothAdapter adapter;
    BluetoothLeScanner scanner;
    ScanCallback scan;
    volatile BluetoothGatt gatt;
    BluetoothGattCharacteristic request,reply;
    volatile boolean ready,writing;
    int generation,scanEpoch;
    public DoorBleClient(Activity activity) { this.activity=activity; }
    public String poll() { String event=events.poll();return event==null?"":event; }
    void emit(String type,String value) { if(events.size()>256){events.clear();events.add("error|overflow");}else events.add(type+"|"+value); }
    boolean permitted() {
        if(Build.VERSION.SDK_INT>=31)return activity.checkSelfPermission(Manifest.permission.BLUETOOTH_SCAN)==PackageManager.PERMISSION_GRANTED && activity.checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT)==PackageManager.PERMISSION_GRANTED;
        return activity.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED;
    }
    public void start(final String address) { handler.post(()->startOnMain(address)); }
    void startOnMain(String address) {
        closeOnMain();events.clear();final int token=generation;
        try {
            if(!permitted()){emit("error","permission");return;}
            BluetoothManager manager=(BluetoothManager)activity.getSystemService(Context.BLUETOOTH_SERVICE);
            adapter=manager==null?null:manager.getAdapter();
            if(adapter==null||!adapter.isEnabled()){emit("error","bluetooth_off");return;}
            if(address!=null&&!address.isEmpty()) {
                if(!BluetoothAdapter.checkBluetoothAddress(address)){emit("error","address");return;}
                connect(adapter.getRemoteDevice(address),token);return;
            }
            beginScan(token,false);
        } catch(Exception e) { fail("start_"+e.getClass().getSimpleName()); }
    }
    // The deployed PICO has previously timed out on service-filtered discovery.
    // Try a bounded software-filtered scan as well; always validate the actual
    // GATT service/characteristics before subscribing or querying. No MAC is baked in.
    void beginScan(final int token,final boolean compatibility) {
        stopScan();final int epoch=scanEpoch;
        scanner=adapter.getBluetoothLeScanner();if(scanner==null){fail("scanner");return;}
        scan=new ScanCallback() {
            @Override public void onScanResult(int type,ScanResult result) {
                handler.post(()->{
                    if(token!=generation||epoch!=scanEpoch||gatt!=null||result==null)return;
                    ScanRecord record=result.getScanRecord();if(record==null)return;
                    List<ParcelUuid> services=record.getServiceUuids();
                    boolean knownService=services!=null&&services.contains(new ParcelUuid(SERVICE));
                    boolean knownName="SuzumeDoor-001".equals(record.getDeviceName());
                    if(!knownService&&!knownName)return;
                    stopScan();connect(result.getDevice(),token);
                });
            }
            @Override public void onScanFailed(int code) {
                handler.post(()->{if(token==generation&&epoch==scanEpoch){
                    if(!compatibility)try{beginScan(token,true);}catch(Exception e){fail("scan_fallback");}
                    else fail("scan_"+code);
                }});
            }
        };
        List<ScanFilter> filters=compatibility?Collections.emptyList():Arrays.asList(
            new ScanFilter.Builder().setServiceUuid(new ParcelUuid(SERVICE)).build(),
            new ScanFilter.Builder().setDeviceName("SuzumeDoor-001").build());
        scanner.startScan(filters,new ScanSettings.Builder().setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY).build(),scan);
        emit("state","scanning");
        handler.postDelayed(()->{if(token==generation&&epoch==scanEpoch&&gatt==null&&scan!=null){
            if(compatibility)fail("scan_timeout");
            else try{beginScan(token,true);}catch(Exception e){fail("scan_fallback");}
        }},6000);
    }
    void connect(BluetoothDevice device,int token) {
        try {
            emit("state","connecting");
            gatt=device.connectGatt(activity,false,callback,BluetoothDevice.TRANSPORT_LE,BluetoothDevice.PHY_LE_1M_MASK,handler);
            if(gatt==null){fail("connect");return;}
            handler.postDelayed(()->{if(token==generation&&!ready)fail("connect_timeout");},15000);
        } catch(Exception e) { fail("connect_"+e.getClass().getSimpleName()); }
    }
    void fail(String reason) { closeOnMain();emit("error",reason); }
    void stopScan() {
        scanEpoch++;
        if(scanner!=null&&scan!=null)try{scanner.stopScan(scan);}catch(Exception ignored){}
        scan=null;scanner=null;
    }
    void closeOnMain() {
        generation++;ready=false;writing=false;stopScan();
        BluetoothGatt old=gatt;gatt=null;request=reply=null;
        if(old!=null){try{old.disconnect();}catch(Exception ignored){}try{old.close();}catch(Exception ignored){}}
    }
    public void close() { handler.post(()->{closeOnMain();events.clear();}); }
    public boolean send(final String line) {
        if(!ready||gatt==null||writing||line==null||!line.matches("[QOCS],[1-9][0-9]{0,4}\\n")||line.length()>20)return false;
        final BluetoothGatt connection=gatt;writing=true;
        handler.post(()->{
            if(connection!=gatt||!ready){writing=false;return;}
            try {
                byte[] data=line.getBytes(StandardCharsets.US_ASCII);boolean accepted;
                if(Build.VERSION.SDK_INT>=33)accepted=connection.writeCharacteristic(request,data,BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT)==BluetoothStatusCodes.SUCCESS;
                else {request.setWriteType(BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT);request.setValue(data);accepted=connection.writeCharacteristic(request);}
                if(!accepted)fail("write_rejected");
            } catch(Exception e) { fail("write_"+e.getClass().getSimpleName()); }
        });
        return true;
    }
    final BluetoothGattCallback callback=new BluetoothGattCallback() {
        @Override public void onConnectionStateChange(BluetoothGatt g,int status,int state) {
            if(g!=gatt)return;
            if(status!=BluetoothGatt.GATT_SUCCESS||state==BluetoothProfile.STATE_DISCONNECTED){fail("disconnected");return;}
            if(state==BluetoothProfile.STATE_CONNECTED)try{if(!g.discoverServices())fail("services_start");}catch(Exception e){fail("services");}
        }
        @Override public void onServicesDiscovered(BluetoothGatt g,int status) {
            if(g!=gatt)return;
            try {
                BluetoothGattService service=g.getService(SERVICE);
                if(status!=0||service==null){fail("service_missing");return;}
                request=service.getCharacteristic(REQUEST);reply=service.getCharacteristic(REPLY);
                if(request==null||reply==null||(request.getProperties()&BluetoothGattCharacteristic.PROPERTY_WRITE)==0||
                    (reply.getProperties()&BluetoothGattCharacteristic.PROPERTY_NOTIFY)==0){fail("characteristics");return;}
                BluetoothGattDescriptor descriptor=reply.getDescriptor(CCCD);
                if(descriptor==null||!g.setCharacteristicNotification(reply,true)){fail("notify_start");return;}
                boolean accepted;
                if(Build.VERSION.SDK_INT>=33)accepted=g.writeDescriptor(descriptor,BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)==BluetoothStatusCodes.SUCCESS;
                else {descriptor.setValue(BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE);accepted=g.writeDescriptor(descriptor);}
                if(!accepted)fail("subscribe_rejected");
            } catch(Exception e){fail("subscribe_"+e.getClass().getSimpleName());}
        }
        @Override public void onDescriptorWrite(BluetoothGatt g,BluetoothGattDescriptor d,int status) {
            if(g!=gatt||!CCCD.equals(d.getUuid()))return;
            if(status!=0){fail("subscribe_"+status);return;}
            ready=true;emit("ready","");
        }
        @Override public void onCharacteristicWrite(BluetoothGatt g,BluetoothGattCharacteristic c,int status) {
            if(g!=gatt)return;writing=false;
            if(status!=0)fail("write_"+status);else emit("written","");
        }
        @Override public void onCharacteristicChanged(BluetoothGatt g,BluetoothGattCharacteristic c) {
            if(Build.VERSION.SDK_INT<33)received(g,c,c.getValue());
        }
        @Override public void onCharacteristicChanged(BluetoothGatt g,BluetoothGattCharacteristic c,byte[] value) { received(g,c,value); }
        void received(BluetoothGatt g,BluetoothGattCharacteristic c,byte[] value) {
            if(g!=gatt||!ready||!REPLY.equals(c.getUuid())||value==null)return;
            for(byte b:value)if((b<32&&b!=10)||b>126){fail("non_ascii");return;}
            emit("data",new String(value,StandardCharsets.US_ASCII));
        }
    };
}
