import torch
from transformers import BertModel, BertConfig

class ProtBERTLanguageModel(torch.nn.Module):
    def __init__(self, config, num_layers=3):
        super(ProtBERTLanguageModel, self).__init__()

        self.protbert = BertModel.from_pretrained("Rostlab/prot_bert_bfd", config=config, ignore_mismatched_sizes=True)
        self.dropout = torch.nn.Dropout(config.hidden_dropout_prob)


        self.concat = torch.nn.Linear(config.hidden_size, config.hidden_size)
        self.layer_norm = torch.nn.LayerNorm(config.hidden_size)
        self.act = torch.nn.ReLU()


        self.additional_layers = torch.nn.ModuleList([
            torch.nn.Linear(config.hidden_size, config.hidden_size) for _ in range(num_layers)
        ])

        self.dense = torch.nn.Linear(config.hidden_size, 1)
        self.sigmoid = torch.nn.Sigmoid()

    def forward(self, inputs, attention_mask):
        outputs = self.protbert(inputs, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output
        x = self.dropout(pooled_output)


        x = self.concat(x)
        x = self.layer_norm(x)
        x = self.act(x)
        x = self.dropout(x)

        for layer in self.additional_layers:
            x = layer(x)
            x = self.layer_norm(x)
            x = self.act(x)
            x = self.dropout(x)

        # Final dense layer
        x = self.dense(x)

        return self.sigmoid(x)


  def create_model(config):
    bert_config = BertConfig(
        vocab_size=config['vocab_size'],
        hidden_size=config['network']['hidden_size'],
        num_hidden_layers=config['network']['hidden_layers'],
        num_attention_heads=config['network']['attn_heads'],
        hidden_dropout_prob=config['network']['dropout']
    )
    model = PeptideBERT(bert_config).to(config['device'])

    return model


  def cri_opt_sch(config, model):
    criterion = torch.nn.BCELoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=config['optim']['lr'])
    scheduler = torch.optim.lr_scheduler.OneCycleLR(
        optimizer,
        max_lr=config['optim']['lr'],
        epochs=config['epochs'],
        steps_per_epoch=config['sch']['steps']
    )

    return criterion, optimizer, scheduler
